###############################################################################
# Simulation: Built-Environment Microbiome → Allergy Response
#
# Calibrated to Hill et al. (2026) - 61 days daily sampling from residential
# sink P-traps showing CV range of 4.9% (stable) to 26.5% (volatile)
#
# Structure:
#   1. Simulate 100 microbial taxa with AR(1) dynamics
#   2. Simulate environmental covariates (temp, humidity, PM2.5, CO2, fungal)
#   3. Tie some taxa abundances to environmental parameters
#   4. Generate allergy scores from causal taxa + environment
#   5. Fit elastic net to recover causal taxa
#   6. Power analysis across study designs and effect sizes
###############################################################################

library(MASS)
library(glmnet)
library(lme4)
library(ggplot2)

set.seed(42)

###############################################################################
# PART 1: SIMULATION ENGINE
###############################################################################

simulate_study <- function(
  n_households   = 20,
  n_persons_per  = 3,       # family members per household
  n_days         = 90,
  n_taxa         = 100,
  n_causal       = 5,       # number of taxa that actually affect allergies
  causal_effects = c(0.10, 0.08, 0.06, 0.04, 0.02),  # log-scale effect sizes
  env_effect_humidity = 0.03,  # direct humidity effect on allergies
  env_effect_pm25     = 0.05,  # direct PM2.5 effect on allergies
  noise_sd       = 0.15,      # residual noise in allergy scores
  person_sd      = 0.30,      # between-person variability in baseline allergies
  household_sd   = 0.20,      # between-household variability
  symptom_ar     = 0.3,       # temporal autocorrelation in allergy symptoms
  verbose        = FALSE
) {

  stopifnot(length(causal_effects) == n_causal)

  #---------------------------------------------------------------------------
  # 1a. Assign each taxon a stability profile (calibrated to Hill et al.)
  #     CV ranges from ~5% (stable, like Sink A) to ~25% (volatile, like Sink B)
  #---------------------------------------------------------------------------
  taxon_names <- paste0("taxon_", sprintf("%03d", 1:n_taxa))

  # Mean log-abundance for each taxon (log-normal, some rare, some abundant)
  taxon_mean_log <- rnorm(n_taxa, mean = -3, sd = 1.5)

  # CV for each taxon: draw from Beta distribution scaled to [0.05, 0.25]
  taxon_cv <- 0.05 + 0.20 * rbeta(n_taxa, shape1 = 2, shape2 = 3)

  # Convert CV to AR(1) parameters
  # Higher CV → lower autocorrelation (more stochastic)
  # AR(1) coefficient: inversely related to CV
  taxon_ar <- pmax(0.05, pmin(0.95, 1 - 3 * taxon_cv))

  # Innovation SD: chosen so stationary variance matches desired CV
  # For AR(1): Var(x) = sigma_innov^2 / (1 - phi^2)
  # We want SD(x) / mean(x) ≈ CV on the abundance scale
  # Working on log scale: SD_log ≈ CV (for small CV)
  taxon_innov_sd <- taxon_cv * sqrt(1 - taxon_ar^2)

  #---------------------------------------------------------------------------
  # 1b. Designate which taxa are environment-linked
  #     Some taxa increase with humidity, some with temperature, etc.
  #---------------------------------------------------------------------------
  # First n_causal taxa are the causal ones (for simplicity)
  causal_idx <- 1:n_causal

  # Some taxa respond to environmental conditions (may overlap with causal)
  # taxon 1-3: increase with humidity (fungal/mold associated)
  # taxon 4-6: increase with temperature (thermophilic)
  # taxon 7-9: increase with PM2.5 (particle-associated)
  humidity_linked  <- c(1, 2, 10, 15, 20)
  temp_linked      <- c(3, 4, 11, 16, 25)
  pm25_linked      <- c(5, 12, 17, 30, 35)

  env_coupling_strength <- 0.3  # how strongly environment drives taxa

  #---------------------------------------------------------------------------
  # 2. Simulate environmental time series (shared within household)
  #---------------------------------------------------------------------------
  all_data <- list()

  for (h in 1:n_households) {

    # Temperature: seasonal trend + daily noise, AR(1)-ish
    day_vec <- 1:n_days
    season_phase <- runif(1, 0, 2 * pi)  # random season start
    temp_base <- 20 + 5 * sin(2 * pi * day_vec / 365 + season_phase)
    temp <- temp_base + arima.sim(list(ar = 0.7), n = n_days, sd = 1.5)
    temp <- as.numeric(temp)

    # Humidity: correlated with temp + own dynamics
    humidity_base <- 50 + 10 * sin(2 * pi * day_vec / 365 + season_phase + pi/4)
    humidity <- humidity_base + 0.5 * (temp - mean(temp)) +
                arima.sim(list(ar = 0.6), n = n_days, sd = 5)
    humidity <- pmax(20, pmin(90, as.numeric(humidity)))

    # PM2.5: episodic spikes on top of baseline
    pm25_base <- 10 + arima.sim(list(ar = 0.5), n = n_days, sd = 3)
    pm25_spikes <- rbinom(n_days, 1, 0.05) * rexp(n_days, 0.05)
    pm25 <- pmax(2, as.numeric(pm25_base) + pm25_spikes)

    # CO2: occupancy-driven, weekly pattern
    co2_base <- 600 + 200 * sin(2 * pi * day_vec / 7) +
                arima.sim(list(ar = 0.4), n = n_days, sd = 50)
    co2 <- pmax(400, as.numeric(co2_base))

    # Fungal concentration: humidity-driven + seasonal
    fungal <- pmax(0, 100 + 2 * (humidity - 50) +
              50 * sin(2 * pi * day_vec / 365 + season_phase) +
              rnorm(n_days, 0, 20))

    #-------------------------------------------------------------------------
    # 3. Simulate microbial taxa for this household
    #    AR(1) dynamics with environmental coupling
    #-------------------------------------------------------------------------
    taxa_matrix <- matrix(0, nrow = n_days, ncol = n_taxa)
    colnames(taxa_matrix) <- taxon_names

    # Household-specific baseline shift
    household_taxon_shift <- rnorm(n_taxa, 0, 0.3)

    for (j in 1:n_taxa) {
      # Initialize
      x <- numeric(n_days)
      x[1] <- taxon_mean_log[j] + household_taxon_shift[j] + rnorm(1, 0, taxon_cv[j])

      for (t in 2:n_days) {
        # AR(1) base dynamics
        x[t] <- taxon_mean_log[j] + household_taxon_shift[j] +
                 taxon_ar[j] * (x[t-1] - taxon_mean_log[j] - household_taxon_shift[j]) +
                 rnorm(1, 0, taxon_innov_sd[j])

        # Environmental coupling
        # Standardize environmental variables for coupling
        humid_z <- (humidity[t] - 50) / 15
        temp_z  <- (temp[t] - 20) / 5
        pm25_z  <- (pm25[t] - 10) / 5

        if (j %in% humidity_linked) {
          x[t] <- x[t] + env_coupling_strength * humid_z * taxon_innov_sd[j]
        }
        if (j %in% temp_linked) {
          x[t] <- x[t] + env_coupling_strength * temp_z * taxon_innov_sd[j]
        }
        if (j %in% pm25_linked) {
          x[t] <- x[t] + env_coupling_strength * pm25_z * taxon_innov_sd[j]
        }
      }
      taxa_matrix[, j] <- x
    }

    #-------------------------------------------------------------------------
    # 4. Generate allergy scores for each person in household
    #-------------------------------------------------------------------------
    for (p in 1:n_persons_per) {

      person_baseline <- rnorm(1, 3, person_sd)  # baseline allergy (1-10 scale)
      household_effect <- rnorm(1, 0, household_sd)

      allergy <- numeric(n_days)
      allergy[1] <- person_baseline + household_effect

      for (t in 2:n_days) {
        # Causal taxa effects (on log-abundance scale → allergy)
        taxa_signal <- sum(causal_effects * taxa_matrix[t, causal_idx])

        # Direct environmental effects
        env_signal <- env_effect_humidity * ((humidity[t] - 50) / 15) +
                      env_effect_pm25 * ((pm25[t] - 10) / 5)

        # Allergy score with temporal autocorrelation
        allergy[t] <- person_baseline + household_effect +
                       taxa_signal + env_signal +
                       symptom_ar * (allergy[t-1] - person_baseline - household_effect) +
                       rnorm(1, 0, noise_sd)
      }

      # Clamp to 1-10 scale
      allergy <- pmax(1, pmin(10, allergy))

      # Build data frame for this person
      person_df <- data.frame(
        household_id = h,
        person_id    = paste0("H", h, "_P", p),
        day          = 1:n_days,
        allergy      = allergy,
        temperature  = temp,
        humidity     = humidity,
        pm25         = pm25,
        co2          = co2,
        fungal_conc  = fungal,
        taxa_matrix
      )
      all_data[[length(all_data) + 1]] <- person_df
    }
  }

  df <- do.call(rbind, all_data)
  df$household_id <- factor(df$household_id)
  df$person_id    <- factor(df$person_id)

  # Return data + metadata
  attr(df, "taxon_names")    <- taxon_names
  attr(df, "causal_idx")     <- causal_idx
  attr(df, "causal_effects") <- causal_effects
  attr(df, "taxon_cv")       <- taxon_cv
  attr(df, "taxon_ar")       <- taxon_ar

  if (verbose) {
    cat(sprintf("Simulated %d households × %d persons × %d days = %d rows\n",
                n_households, n_persons_per, n_days, nrow(df)))
    cat(sprintf("Causal taxa: %s\n", paste(taxon_names[causal_idx], collapse=", ")))
    cat(sprintf("Effect sizes: %s\n", paste(causal_effects, collapse=", ")))
  }

  return(df)
}


###############################################################################
# PART 2: MODEL FITTING — ELASTIC NET
###############################################################################

fit_elastic_net <- function(df, taxon_names, alpha = 0.5) {
  # Prepare predictor matrix:
  #   - All 100 taxa (CLR-transformed would be ideal, but log-abundances for now)
  #   - Environmental covariates
  #   - Residualize out person random effects first (demean by person)

  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  pred_vars <- c(taxon_names, env_vars)

  # Person-level demeaning (removes person random effects)
  df_demeaned <- df
  for (v in c("allergy", pred_vars)) {
    person_means <- tapply(df[[v]], df$person_id, mean)
    df_demeaned[[v]] <- df[[v]] - person_means[as.character(df$person_id)]
  }

  X <- as.matrix(df_demeaned[, pred_vars])
  y <- df_demeaned$allergy

  # Remove any columns with zero or near-zero variance before scaling
  col_sds <- apply(X, 2, sd)
  good_cols <- col_sds > 1e-10
  X <- X[, good_cols]

  # Remove any rows with NA/NaN/Inf
  finite_rows <- complete.cases(X) & is.finite(y)
  X <- X[finite_rows, ]
  y <- y[finite_rows]

  # Standardize X
  X_scaled <- scale(X)

  # Ensure y is a plain numeric vector (avoids cv.glmnet dimension issues)
  y <- as.numeric(y)

  # Fit elastic net with cross-validation (use explicit foldid for stability)
  n <- length(y)
  foldid <- sample(rep(1:10, length.out = n))
  cv_fit <- cv.glmnet(X_scaled, y, alpha = alpha, foldid = foldid)

  # Extract coefficients at lambda.1se (more parsimonious)
  coefs <- as.numeric(coef(cv_fit, s = "lambda.1se"))[-1]  # drop intercept
  names(coefs) <- colnames(X_scaled)

  # Also get lambda.min coefficients (less regularized)
  coefs_min <- as.numeric(coef(cv_fit, s = "lambda.min"))[-1]
  names(coefs_min) <- colnames(X_scaled)

  return(list(
    cv_fit     = cv_fit,
    coefs_1se  = coefs,
    coefs_min  = coefs_min,
    pred_names = colnames(X_scaled)
  ))
}


###############################################################################
# PART 3: EVALUATE RECOVERY OF CAUSAL TAXA
###############################################################################

evaluate_recovery <- function(fit_result, causal_idx, taxon_names, threshold = 0) {
  coefs <- fit_result$coefs_min  # use less regularized for sensitivity

  # Identify which taxa were selected (non-zero coefficient)
  taxa_coefs <- coefs[taxon_names[taxon_names %in% names(coefs)]]
  selected <- names(taxa_coefs[abs(taxa_coefs) > threshold])
  true_causal <- taxon_names[causal_idx]

  tp <- sum(true_causal %in% selected)
  fp <- sum(!(selected %in% true_causal) & selected %in% taxon_names)
  fn <- sum(!(true_causal %in% selected))
  tn <- length(taxon_names) - tp - fp - fn

  sensitivity <- tp / max(1, tp + fn)
  specificity <- tn / max(1, tn + fp)
  fdr <- fp / max(1, tp + fp)

  # Rank of causal taxa by absolute coefficient
  taxa_ranked <- sort(abs(taxa_coefs), decreasing = TRUE)
  causal_ranks <- match(true_causal, names(taxa_ranked))

  return(list(
    sensitivity   = sensitivity,
    specificity   = specificity,
    fdr           = fdr,
    tp = tp, fp = fp, fn = fn, tn = tn,
    n_selected    = length(selected),
    causal_ranks  = causal_ranks,
    taxa_coefs    = taxa_coefs
  ))
}


###############################################################################
# PART 4: POWER ANALYSIS — VARY STUDY DESIGN PARAMETERS
###############################################################################

run_power_analysis <- function(
  n_sims          = 50,
  households_vec  = c(5, 10, 20, 40),
  days_vec        = c(30, 60, 90, 180),
  effects_scales  = c(0.5, 1.0, 1.5, 2.0),  # multipliers on base effects
  base_effects    = c(0.10, 0.08, 0.06, 0.04, 0.02),
  n_persons_per   = 3,
  verbose         = TRUE
) {

  results <- data.frame()

  # Vary one parameter at a time, holding others at default
  default_hh   <- 20
  default_days <- 90
  default_scale <- 1.0

  #--- Vary number of households ---
  if (verbose) cat("\n=== Varying number of households ===\n")
  for (nh in households_vec) {
    for (sim in 1:n_sims) {
      df <- simulate_study(
        n_households   = nh,
        n_persons_per  = n_persons_per,
        n_days         = default_days,
        causal_effects = base_effects * default_scale
      )
      fit <- fit_elastic_net(df, attr(df, "taxon_names"))
      eval <- evaluate_recovery(fit, attr(df, "causal_idx"), attr(df, "taxon_names"))

      results <- rbind(results, data.frame(
        vary       = "households",
        value      = nh,
        sim        = sim,
        sensitivity = eval$sensitivity,
        specificity = eval$specificity,
        fdr         = eval$fdr,
        n_selected  = eval$n_selected
      ))
    }
    if (verbose) cat(sprintf("  households=%d done\n", nh))
  }

  #--- Vary number of days ---
  if (verbose) cat("\n=== Varying number of days ===\n")
  for (nd in days_vec) {
    for (sim in 1:n_sims) {
      df <- simulate_study(
        n_households   = default_hh,
        n_persons_per  = n_persons_per,
        n_days         = nd,
        causal_effects = base_effects * default_scale
      )
      fit <- fit_elastic_net(df, attr(df, "taxon_names"))
      eval <- evaluate_recovery(fit, attr(df, "causal_idx"), attr(df, "taxon_names"))

      results <- rbind(results, data.frame(
        vary       = "days",
        value      = nd,
        sim        = sim,
        sensitivity = eval$sensitivity,
        specificity = eval$specificity,
        fdr         = eval$fdr,
        n_selected  = eval$n_selected
      ))
    }
    if (verbose) cat(sprintf("  days=%d done\n", nd))
  }

  #--- Vary effect size ---
  if (verbose) cat("\n=== Varying effect size ===\n")
  for (es in effects_scales) {
    for (sim in 1:n_sims) {
      df <- simulate_study(
        n_households   = default_hh,
        n_persons_per  = n_persons_per,
        n_days         = default_days,
        causal_effects = base_effects * es
      )
      fit <- fit_elastic_net(df, attr(df, "taxon_names"))
      eval <- evaluate_recovery(fit, attr(df, "causal_idx"), attr(df, "taxon_names"))

      results <- rbind(results, data.frame(
        vary       = "effect_size",
        value      = es,
        sim        = sim,
        sensitivity = eval$sensitivity,
        specificity = eval$specificity,
        fdr         = eval$fdr,
        n_selected  = eval$n_selected
      ))
    }
    if (verbose) cat(sprintf("  effect_scale=%.1f done\n", es))
  }

  return(results)
}


###############################################################################
# PART 5: VISUALIZATION
###############################################################################

plot_simulated_data <- function(df, output_prefix = "sim") {

  taxon_names   <- attr(df, "taxon_names")
  causal_idx    <- attr(df, "causal_idx")
  causal_names  <- taxon_names[causal_idx]

  # Pick one household, one person for time series plots
  one_person <- levels(df$person_id)[1]
  df_one <- df[df$person_id == one_person, ]

  #--- Plot 1: Allergy score over time ---
  p1 <- ggplot(df_one, aes(x = day, y = allergy)) +
    geom_line(color = "firebrick", linewidth = 0.8) +
    geom_point(size = 0.5) +
    labs(title = paste("Daily Allergy Score —", one_person),
         x = "Day", y = "Allergy Score (1-10)") +
    theme_minimal()
  ggsave(paste0(output_prefix, "_allergy_timeseries.png"), p1, width = 10, height = 4)

  #--- Plot 2: Causal taxa dynamics ---
  taxa_long <- do.call(rbind, lapply(causal_names, function(tn) {
    data.frame(day = df_one$day, log_abundance = df_one[[tn]], taxon = tn)
  }))
  p2 <- ggplot(taxa_long, aes(x = day, y = log_abundance, color = taxon)) +
    geom_line(linewidth = 0.6) +
    labs(title = "Causal Taxa — Log-Abundance Over Time",
         x = "Day", y = "Log Abundance", color = "Taxon") +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave(paste0(output_prefix, "_causal_taxa_dynamics.png"), p2, width = 10, height = 5)

  #--- Plot 3: Environmental covariates ---
  env_vars <- c("temperature", "humidity", "pm25", "fungal_conc")
  env_labels <- c("Temperature (C)", "Humidity (%)", "PM2.5 (ug/m3)", "Fungal (spores/m3)")
  env_long <- do.call(rbind, lapply(seq_along(env_vars), function(i) {
    data.frame(day = df_one$day, value = df_one[[env_vars[i]]], variable = env_labels[i])
  }))
  p3 <- ggplot(env_long, aes(x = day, y = value)) +
    geom_line(color = "steelblue", linewidth = 0.6) +
    facet_wrap(~ variable, scales = "free_y", ncol = 2) +
    labs(title = "Environmental Covariates Over Time",
         x = "Day", y = "Value") +
    theme_minimal()
  ggsave(paste0(output_prefix, "_environmental.png"), p3, width = 10, height = 6)

  #--- Plot 4: Allergy vs causal taxon scatterplots ---
  scatter_long <- do.call(rbind, lapply(causal_names, function(tn) {
    data.frame(allergy = df$allergy, log_abundance = df[[tn]], taxon = tn)
  }))
  p4 <- ggplot(scatter_long, aes(x = log_abundance, y = allergy)) +
    geom_point(alpha = 0.1, size = 0.5) +
    geom_smooth(method = "lm", color = "red", linewidth = 0.8) +
    facet_wrap(~ taxon, scales = "free_x") +
    labs(title = "Allergy Score vs Causal Taxa Abundance (all persons)",
         x = "Log Abundance", y = "Allergy Score") +
    theme_minimal()
  ggsave(paste0(output_prefix, "_scatter_causal.png"), p4, width = 10, height = 6)

  cat("Saved 4 plots with prefix:", output_prefix, "\n")
}


plot_model_coefficients <- function(fit_result, causal_idx, taxon_names,
                                    output_file = "sim_coefficients.png") {
  coefs <- fit_result$coefs_min
  taxa_coefs <- coefs[names(coefs) %in% taxon_names]

  coef_df <- data.frame(
    taxon = names(taxa_coefs),
    coefficient = as.numeric(taxa_coefs),
    is_causal = names(taxa_coefs) %in% taxon_names[causal_idx]
  )
  coef_df <- coef_df[order(abs(coef_df$coefficient), decreasing = TRUE), ]
  # Show top 20
  coef_df_top <- head(coef_df, 20)
  coef_df_top$taxon <- factor(coef_df_top$taxon, levels = rev(coef_df_top$taxon))

  p <- ggplot(coef_df_top, aes(x = coefficient, y = taxon, fill = is_causal)) +
    geom_col() +
    scale_fill_manual(values = c("FALSE" = "grey60", "TRUE" = "firebrick"),
                      labels = c("Non-causal", "Causal"),
                      name = "True Status") +
    labs(title = "Top 20 Elastic Net Coefficients (taxa only)",
         x = "Coefficient", y = "") +
    theme_minimal() +
    geom_vline(xintercept = 0, linetype = "dashed")
  ggsave(output_file, p, width = 8, height = 6)
  cat("Saved coefficient plot:", output_file, "\n")
}


plot_power_curves <- function(power_results, output_file = "sim_power_curves.png") {
  # Summarize across simulations
  summary_df <- aggregate(
    cbind(sensitivity, specificity, fdr) ~ vary + value,
    data = power_results,
    FUN = function(x) c(mean = mean(x), se = sd(x) / sqrt(length(x)))
  )

  # Flatten the matrix columns
  power_long <- do.call(rbind, lapply(unique(power_results$vary), function(v) {
    sub <- power_results[power_results$vary == v, ]
    agg <- aggregate(
      cbind(sensitivity, specificity, fdr) ~ value,
      data = sub,
      FUN = mean
    )
    agg_se <- aggregate(
      cbind(sensitivity, specificity, fdr) ~ value,
      data = sub,
      FUN = function(x) sd(x) / sqrt(length(x))
    )
    data.frame(
      vary        = v,
      value       = agg$value,
      sensitivity = agg$sensitivity,
      sens_se     = agg_se$sensitivity,
      specificity = agg$specificity,
      spec_se     = agg_se$specificity,
      fdr         = agg$fdr,
      fdr_se      = agg_se$fdr
    )
  }))

  # Nice labels
  power_long$vary_label <- factor(power_long$vary,
    levels = c("households", "days", "effect_size"),
    labels = c("Number of Households", "Days of Sampling", "Effect Size Multiplier"))

  p <- ggplot(power_long, aes(x = value)) +
    geom_line(aes(y = sensitivity, color = "Sensitivity"), linewidth = 1) +
    geom_point(aes(y = sensitivity, color = "Sensitivity")) +
    geom_errorbar(aes(ymin = sensitivity - 1.96 * sens_se,
                      ymax = sensitivity + 1.96 * sens_se,
                      color = "Sensitivity"), width = 0) +
    geom_line(aes(y = 1 - fdr, color = "1 - FDR"), linewidth = 1) +
    geom_point(aes(y = 1 - fdr, color = "1 - FDR")) +
    geom_errorbar(aes(ymin = 1 - fdr - 1.96 * fdr_se,
                      ymax = 1 - fdr + 1.96 * fdr_se,
                      color = "1 - FDR"), width = 0) +
    facet_wrap(~ vary_label, scales = "free_x") +
    geom_hline(yintercept = 0.8, linetype = "dashed", color = "grey50") +
    scale_color_manual(values = c("Sensitivity" = "firebrick", "1 - FDR" = "steelblue")) +
    ylim(0, 1) +
    labs(title = "Power Analysis: Detecting Causal Taxa",
         subtitle = "Dashed line = 80% power threshold",
         x = "Parameter Value", y = "Rate", color = "") +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave(output_file, p, width = 12, height = 5)
  cat("Saved power curve plot:", output_file, "\n")
}


###############################################################################
# PART 6: RUN EVERYTHING
###############################################################################

cat("================================================================\n")
cat("  Microbiome-Allergy Simulation Framework\n")
cat("  Calibrated to Hill et al. (2026) temporal dynamics\n")
cat("================================================================\n\n")

#--- Step 1: Single simulation + visualization ---
cat("--- Step 1: Generating simulated data ---\n")
df <- simulate_study(
  n_households   = 20,
  n_persons_per  = 3,
  n_days         = 90,
  causal_effects = c(0.10, 0.08, 0.06, 0.04, 0.02),
  verbose        = TRUE
)

cat("\n--- Step 2: Plotting simulated data ---\n")
plot_simulated_data(df, output_prefix = "sim")

#--- Step 3: Fit model ---
cat("\n--- Step 3: Fitting elastic net ---\n")
fit <- fit_elastic_net(df, attr(df, "taxon_names"))
eval <- evaluate_recovery(fit, attr(df, "causal_idx"), attr(df, "taxon_names"))

cat(sprintf("  Sensitivity: %.1f%% (%d/%d causal taxa detected)\n",
            100 * eval$sensitivity, eval$tp, eval$tp + eval$fn))
cat(sprintf("  Specificity: %.1f%%\n", 100 * eval$specificity))
cat(sprintf("  FDR: %.1f%% (%d false positives out of %d selected)\n",
            100 * eval$fdr, eval$fp, eval$tp + eval$fp))
cat(sprintf("  Causal taxa ranks: %s\n",
            paste(eval$causal_ranks, collapse = ", ")))

plot_model_coefficients(fit, attr(df, "causal_idx"), attr(df, "taxon_names"))

#--- Step 4: Power analysis ---
cat("\n--- Step 4: Running power analysis (this will take a few minutes) ---\n")
cat("  50 simulations × 12 parameter settings = 600 total fits\n\n")

power_results <- run_power_analysis(
  n_sims         = 50,
  households_vec = c(5, 10, 20, 40),
  days_vec       = c(30, 60, 90, 180),
  effects_scales = c(0.5, 1.0, 1.5, 2.0),
  base_effects   = c(0.10, 0.08, 0.06, 0.04, 0.02)
)

cat("\n--- Step 5: Plotting power curves ---\n")
plot_power_curves(power_results)

#--- Save results ---
write.csv(power_results, "power_results.csv", row.names = FALSE)
cat("\nSaved power_results.csv\n")

cat("\n================================================================\n")
cat("  Done! Output files:\n")
cat("  - sim_allergy_timeseries.png\n")
cat("  - sim_causal_taxa_dynamics.png\n")
cat("  - sim_environmental.png\n")
cat("  - sim_scatter_causal.png\n")
cat("  - sim_coefficients.png\n")
cat("  - sim_power_curves.png\n")
cat("  - power_results.csv\n")
cat("================================================================\n")
