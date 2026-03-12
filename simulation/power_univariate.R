###############################################################################
# Power Analysis: Univariate models with BH FDR correction
# Vary number of households, track TP/FP/FDR across simulations
###############################################################################

library(MASS)
library(glmnet)
library(lme4)
library(ggplot2)

set.seed(42)

# Source simulation functions
source_lines <- readLines("sim_microbiome_allergies.R")
part6_line <- grep("PART 6: RUN EVERYTHING", source_lines)
tmp <- tempfile(fileext = ".R")
writeLines(source_lines[1:(part6_line - 1)], tmp)
source(tmp)

###############################################################################
# Per-taxon model fitting functions (streamlined)
###############################################################################

run_univariate <- function(df, taxon_names, adjust_covariates = FALSE) {
  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  all_vars <- c(taxon_names, env_vars)

  # Person-level demeaning
  df_dm <- df
  for (v in c("allergy", all_vars)) {
    pm <- tapply(df[[v]], df$person_id, mean)
    df_dm[[v]] <- df[[v]] - pm[as.character(df$person_id)]
  }

  pvals <- numeric(length(taxon_names))
  coefs <- numeric(length(taxon_names))

  for (i in seq_along(taxon_names)) {
    v <- taxon_names[i]
    if (adjust_covariates) {
      mod_df <- data.frame(
        allergy = df_dm$allergy, taxon = df_dm[[v]],
        temperature = df_dm$temperature, humidity = df_dm$humidity,
        pm25 = df_dm$pm25, co2 = df_dm$co2, fungal_conc = df_dm$fungal_conc
      )
      mod <- lm(allergy ~ taxon + temperature + humidity + pm25 + co2 + fungal_conc,
                data = mod_df)
      s <- summary(mod)
      coefs[i] <- s$coefficients["taxon", "Estimate"]
      pvals[i] <- s$coefficients["taxon", "Pr(>|t|)"]
    } else {
      mod <- lm(allergy ~ x, data = data.frame(allergy = df_dm$allergy, x = df_dm[[v]]))
      s <- summary(mod)
      coefs[i] <- s$coefficients["x", "Estimate"]
      pvals[i] <- s$coefficients["x", "Pr(>|t|)"]
    }
  }

  fdr <- p.adjust(pvals, method = "BH")
  return(data.frame(variable = taxon_names, coefficient = coefs,
                    p_value = pvals, fdr = fdr, stringsAsFactors = FALSE))
}

###############################################################################
# Power analysis: vary households, days, effect size
###############################################################################

cat("================================================================\n")
cat("  Power Analysis: Univariate Models with BH FDR\n")
cat("================================================================\n\n")

n_sims <- 50
households_vec <- c(5, 10, 20, 40, 80, 160)
days_vec <- c(30, 60, 90, 180, 365)
effect_scales <- c(0.5, 1.0, 1.5, 2.0)
base_effects <- c(0.10, 0.08, 0.06, 0.04, 0.02)

default_hh <- 20
default_days <- 90
default_scale <- 1.0

results <- data.frame()

# --- Vary households ---
cat("=== Varying households ===\n")
for (nh in households_vec) {
  for (sim in 1:n_sims) {
    df <- simulate_study(n_households = nh, n_persons_per = 3, n_days = default_days,
                         causal_effects = base_effects * default_scale)
    tn <- attr(df, "taxon_names")
    ci <- attr(df, "causal_idx")
    cn <- tn[ci]

    for (adj in c(FALSE, TRUE)) {
      res <- run_univariate(df, tn, adjust_covariates = adj)
      model_name <- ifelse(adj, "Covariate-adjusted", "Simple univariate")

      for (threshold in c(0.05, 0.10, 0.20)) {
        sig <- res[res$fdr < threshold, ]
        tp <- sum(sig$variable %in% cn)
        fp <- sum(!(sig$variable %in% cn))
        results <- rbind(results, data.frame(
          vary = "households", value = nh, sim = sim,
          model = model_name, fdr_threshold = threshold,
          sensitivity = tp / length(cn),
          false_positives = fp,
          n_significant = nrow(sig),
          observed_fdr = ifelse(nrow(sig) > 0, fp / nrow(sig), 0)
        ))
      }
    }
  }
  cat(sprintf("  households=%d done\n", nh))
}

# --- Vary days ---
cat("\n=== Varying days ===\n")
for (nd in days_vec) {
  for (sim in 1:n_sims) {
    df <- simulate_study(n_households = default_hh, n_persons_per = 3, n_days = nd,
                         causal_effects = base_effects * default_scale)
    tn <- attr(df, "taxon_names")
    ci <- attr(df, "causal_idx")
    cn <- tn[ci]

    for (adj in c(FALSE, TRUE)) {
      res <- run_univariate(df, tn, adjust_covariates = adj)
      model_name <- ifelse(adj, "Covariate-adjusted", "Simple univariate")

      for (threshold in c(0.05, 0.10, 0.20)) {
        sig <- res[res$fdr < threshold, ]
        tp <- sum(sig$variable %in% cn)
        fp <- sum(!(sig$variable %in% cn))
        results <- rbind(results, data.frame(
          vary = "days", value = nd, sim = sim,
          model = model_name, fdr_threshold = threshold,
          sensitivity = tp / length(cn),
          false_positives = fp,
          n_significant = nrow(sig),
          observed_fdr = ifelse(nrow(sig) > 0, fp / nrow(sig), 0)
        ))
      }
    }
  }
  cat(sprintf("  days=%d done\n", nd))
}

# --- Vary effect size ---
cat("\n=== Varying effect size ===\n")
for (es in effect_scales) {
  for (sim in 1:n_sims) {
    df <- simulate_study(n_households = default_hh, n_persons_per = 3, n_days = default_days,
                         causal_effects = base_effects * es)
    tn <- attr(df, "taxon_names")
    ci <- attr(df, "causal_idx")
    cn <- tn[ci]

    for (adj in c(FALSE, TRUE)) {
      res <- run_univariate(df, tn, adjust_covariates = adj)
      model_name <- ifelse(adj, "Covariate-adjusted", "Simple univariate")

      for (threshold in c(0.05, 0.10, 0.20)) {
        sig <- res[res$fdr < threshold, ]
        tp <- sum(sig$variable %in% cn)
        fp <- sum(!(sig$variable %in% cn))
        results <- rbind(results, data.frame(
          vary = "effect_size", value = es, sim = sim,
          model = model_name, fdr_threshold = threshold,
          sensitivity = tp / length(cn),
          false_positives = fp,
          n_significant = nrow(sig),
          observed_fdr = ifelse(nrow(sig) > 0, fp / nrow(sig), 0)
        ))
      }
    }
  }
  cat(sprintf("  effect_scale=%.1f done\n", es))
}

write.csv(results, "power_univariate_results.csv", row.names = FALSE)
cat("\nSaved power_univariate_results.csv\n")

###############################################################################
# Plotting
###############################################################################

# Summarize
agg <- aggregate(
  cbind(sensitivity, false_positives, observed_fdr) ~ vary + value + model + fdr_threshold,
  data = results, FUN = mean
)
agg_se <- aggregate(
  cbind(sensitivity, false_positives, observed_fdr) ~ vary + value + model + fdr_threshold,
  data = results, FUN = function(x) sd(x) / sqrt(length(x))
)

# Merge
names(agg_se)[5:7] <- paste0(names(agg_se)[5:7], "_se")
plotdata <- merge(agg, agg_se)

# --- Plot 1: Sensitivity vs households (FDR < 0.05) ---
sub <- plotdata[plotdata$vary == "households" & plotdata$fdr_threshold == 0.05, ]
p1 <- ggplot(sub, aes(x = value, y = sensitivity, color = model)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = sensitivity - 1.96 * sensitivity_se,
                    ymax = pmin(1, sensitivity + 1.96 * sensitivity_se)),
                width = 0) +
  geom_hline(yintercept = 0.8, linetype = "dashed", color = "grey50") +
  scale_color_brewer(palette = "Set1") +
  ylim(0, 1) +
  labs(title = "Sensitivity vs Number of Households (BH FDR < 0.05)",
       x = "Number of Households", y = "Sensitivity (causal taxa detected / 5)",
       color = "Model") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("power_univ_sensitivity_households.png", p1, width = 10, height = 6)

# --- Plot 2: False positives vs households (FDR < 0.05) ---
p2 <- ggplot(sub, aes(x = value, y = false_positives, color = model)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, false_positives - 1.96 * false_positives_se),
                    ymax = false_positives + 1.96 * false_positives_se),
                width = 0) +
  scale_color_brewer(palette = "Set1") +
  labs(title = "False Positives vs Number of Households (BH FDR < 0.05)",
       x = "Number of Households", y = "False Positives (out of 95 non-causal)",
       color = "Model") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("power_univ_fp_households.png", p2, width = 10, height = 6)

# --- Plot 3: Observed FDR vs households ---
p3 <- ggplot(sub, aes(x = value, y = observed_fdr, color = model)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, observed_fdr - 1.96 * observed_fdr_se),
                    ymax = pmin(1, observed_fdr + 1.96 * observed_fdr_se)),
                width = 0) +
  geom_hline(yintercept = 0.05, linetype = "dashed", color = "red") +
  annotate("text", x = max(sub$value) * 0.9, y = 0.08,
           label = "Nominal FDR = 0.05", color = "red", size = 3) +
  scale_color_brewer(palette = "Set1") +
  ylim(0, 1) +
  labs(title = "Observed FDR vs Number of Households (BH threshold = 0.05)",
       subtitle = "How well does BH actually control FDR?",
       x = "Number of Households", y = "Observed FDR (FP / total significant)",
       color = "Model") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("power_univ_observed_fdr_households.png", p3, width = 10, height = 6)

# --- Plot 4: Multi-panel — sensitivity, FP, observed FDR for all three vary dimensions ---
# At FDR < 0.05, covariate-adjusted model only
sub_adj <- plotdata[plotdata$model == "Covariate-adjusted" & plotdata$fdr_threshold == 0.05, ]
sub_adj$vary_label <- factor(sub_adj$vary,
  levels = c("households", "days", "effect_size"),
  labels = c("Number of Households", "Days of Sampling", "Effect Size Multiplier"))

# Sensitivity panel
p4a <- ggplot(sub_adj, aes(x = value, y = sensitivity)) +
  geom_line(color = "firebrick", linewidth = 1) +
  geom_point(color = "firebrick", size = 2.5) +
  geom_errorbar(aes(ymin = sensitivity - 1.96 * sensitivity_se,
                    ymax = pmin(1, sensitivity + 1.96 * sensitivity_se)),
                color = "firebrick", width = 0) +
  facet_wrap(~ vary_label, scales = "free_x") +
  geom_hline(yintercept = 0.8, linetype = "dashed", color = "grey50") +
  ylim(0, 1) +
  labs(title = "Covariate-Adjusted Univariate: Sensitivity (BH FDR < 0.05)",
       x = "Parameter Value", y = "Sensitivity") +
  theme_minimal()
ggsave("power_univ_sensitivity_all.png", p4a, width = 12, height = 4)

# FP panel
p4b <- ggplot(sub_adj, aes(x = value, y = false_positives)) +
  geom_line(color = "steelblue", linewidth = 1) +
  geom_point(color = "steelblue", size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, false_positives - 1.96 * false_positives_se),
                    ymax = false_positives + 1.96 * false_positives_se),
                color = "steelblue", width = 0) +
  facet_wrap(~ vary_label, scales = "free_x") +
  labs(title = "Covariate-Adjusted Univariate: False Positives (BH FDR < 0.05)",
       x = "Parameter Value", y = "False Positives") +
  theme_minimal()
ggsave("power_univ_fp_all.png", p4b, width = 12, height = 4)

# Observed FDR panel
p4c <- ggplot(sub_adj, aes(x = value, y = observed_fdr)) +
  geom_line(color = "darkorange", linewidth = 1) +
  geom_point(color = "darkorange", size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, observed_fdr - 1.96 * observed_fdr_se),
                    ymax = pmin(1, observed_fdr + 1.96 * observed_fdr_se)),
                color = "darkorange", width = 0) +
  facet_wrap(~ vary_label, scales = "free_x") +
  geom_hline(yintercept = 0.05, linetype = "dashed", color = "red") +
  ylim(0, 1) +
  labs(title = "Covariate-Adjusted Univariate: Observed FDR (BH threshold = 0.05)",
       x = "Parameter Value", y = "Observed FDR") +
  theme_minimal()
ggsave("power_univ_observed_fdr_all.png", p4c, width = 12, height = 4)

cat("\nSaved all power analysis plots\n")

# --- Print summary table ---
cat("\n================================================================\n")
cat("  Summary: Covariate-Adjusted Model at BH FDR < 0.05\n")
cat("================================================================\n\n")

cat("--- By Number of Households ---\n")
sub_hh <- plotdata[plotdata$vary == "households" & plotdata$model == "Covariate-adjusted"
                   & plotdata$fdr_threshold == 0.05, ]
for (i in 1:nrow(sub_hh)) {
  cat(sprintf("  HH=%3d: sensitivity=%.2f, FP=%.1f, observed_FDR=%.3f\n",
              sub_hh$value[i], sub_hh$sensitivity[i],
              sub_hh$false_positives[i], sub_hh$observed_fdr[i]))
}

cat("\n--- By Days ---\n")
sub_d <- plotdata[plotdata$vary == "days" & plotdata$model == "Covariate-adjusted"
                  & plotdata$fdr_threshold == 0.05, ]
for (i in 1:nrow(sub_d)) {
  cat(sprintf("  Days=%3d: sensitivity=%.2f, FP=%.1f, observed_FDR=%.3f\n",
              sub_d$value[i], sub_d$sensitivity[i],
              sub_d$false_positives[i], sub_d$observed_fdr[i]))
}

cat("\n--- By Effect Size ---\n")
sub_e <- plotdata[plotdata$vary == "effect_size" & plotdata$model == "Covariate-adjusted"
                  & plotdata$fdr_threshold == 0.05, ]
for (i in 1:nrow(sub_e)) {
  cat(sprintf("  Scale=%.1f: sensitivity=%.2f, FP=%.1f, observed_FDR=%.3f\n",
              sub_e$value[i], sub_e$sensitivity[i],
              sub_e$false_positives[i], sub_e$observed_fdr[i]))
}

cat("\n================================================================\n")
cat("  Done!\n")
cat("================================================================\n")
