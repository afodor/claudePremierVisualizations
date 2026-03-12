###############################################################################
# Mixed-Effects Linear Models: Per-taxon with random effects + env covariates
#
# For each of 100 taxa, fit:
#   allergy ~ taxon + temperature + humidity + pm25 + co2 + fungal_conc
#            + (1|household_id/person_id)
#
# Compare to: simple univariate (no covariates, no random effects)
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
# MODEL 1: Simple univariate (demeaned, no covariates) — baseline
###############################################################################

fit_simple_univariate <- function(df, taxon_names) {
  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  all_vars <- c(taxon_names, env_vars)

  # Person-level demeaning
  df_dm <- df
  for (v in c("allergy", all_vars)) {
    pm <- tapply(df[[v]], df$person_id, mean)
    df_dm[[v]] <- df[[v]] - pm[as.character(df$person_id)]
  }

  results <- list()
  for (v in taxon_names) {
    mod <- lm(allergy ~ x, data = data.frame(allergy = df_dm$allergy, x = df_dm[[v]]))
    s <- summary(mod)
    coef_row <- s$coefficients["x", ]
    results[[v]] <- data.frame(
      variable = v, coefficient = coef_row["Estimate"],
      p_value = coef_row["Pr(>|t|)"], r_squared = s$r.squared,
      model = "Simple univariate", stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, results)
  out$fdr <- p.adjust(out$p_value, method = "BH")
  rownames(out) <- NULL
  return(out)
}

###############################################################################
# MODEL 2: Univariate + environmental covariates (demeaned)
###############################################################################

fit_covariate_adjusted <- function(df, taxon_names) {
  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  all_vars <- c(taxon_names, env_vars)

  # Person-level demeaning
  df_dm <- df
  for (v in c("allergy", all_vars)) {
    pm <- tapply(df[[v]], df$person_id, mean)
    df_dm[[v]] <- df[[v]] - pm[as.character(df$person_id)]
  }

  results <- list()
  for (v in taxon_names) {
    mod_df <- data.frame(
      allergy = df_dm$allergy, taxon = df_dm[[v]],
      temperature = df_dm$temperature, humidity = df_dm$humidity,
      pm25 = df_dm$pm25, co2 = df_dm$co2, fungal_conc = df_dm$fungal_conc
    )
    mod <- lm(allergy ~ taxon + temperature + humidity + pm25 + co2 + fungal_conc,
              data = mod_df)
    s <- summary(mod)
    coef_row <- s$coefficients["taxon", ]
    results[[v]] <- data.frame(
      variable = v, coefficient = coef_row["Estimate"],
      p_value = coef_row["Pr(>|t|)"], r_squared = s$r.squared,
      model = "Covariate-adjusted", stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, results)
  out$fdr <- p.adjust(out$p_value, method = "BH")
  rownames(out) <- NULL
  return(out)
}

###############################################################################
# MODEL 3: Mixed-effects with random intercepts (no env covariates)
###############################################################################

fit_mixed_effects <- function(df, taxon_names) {
  results <- list()
  for (v in taxon_names) {
    mod_df <- data.frame(
      allergy = df$allergy, taxon = df[[v]],
      person_id = df$person_id, household_id = df$household_id
    )
    mod <- lmer(allergy ~ taxon + (1|household_id/person_id), data = mod_df)
    s <- summary(mod)
    coef_row <- s$coefficients["taxon", ]
    # lmer doesn't give p-values by default; use Satterthwaite approx via t-as-z
    t_val <- coef_row["t value"]
    p_val <- 2 * pnorm(abs(t_val), lower.tail = FALSE)
    results[[v]] <- data.frame(
      variable = v, coefficient = coef_row["Estimate"],
      p_value = p_val, r_squared = NA,
      model = "Mixed-effects", stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, results)
  out$fdr <- p.adjust(out$p_value, method = "BH")
  rownames(out) <- NULL
  return(out)
}

###############################################################################
# MODEL 4: Mixed-effects + environmental covariates (the full model)
###############################################################################

fit_mixed_effects_adjusted <- function(df, taxon_names) {
  results <- list()
  for (v in taxon_names) {
    mod_df <- data.frame(
      allergy = df$allergy, taxon = df[[v]],
      temperature = df$temperature, humidity = df$humidity,
      pm25 = df$pm25, co2 = df$co2, fungal_conc = df$fungal_conc,
      person_id = df$person_id, household_id = df$household_id
    )
    mod <- lmer(allergy ~ taxon + temperature + humidity + pm25 + co2 + fungal_conc
                + (1|household_id/person_id), data = mod_df)
    s <- summary(mod)
    coef_row <- s$coefficients["taxon", ]
    t_val <- coef_row["t value"]
    p_val <- 2 * pnorm(abs(t_val), lower.tail = FALSE)
    results[[v]] <- data.frame(
      variable = v, coefficient = coef_row["Estimate"],
      p_value = p_val, r_squared = NA,
      model = "Mixed + covariates", stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, results)
  out$fdr <- p.adjust(out$p_value, method = "BH")
  rownames(out) <- NULL
  return(out)
}

###############################################################################
# COMPARISON PLOTS
###############################################################################

plot_model_comparison <- function(all_results, causal_idx, taxon_names,
                                  fdr_threshold = 0.05) {
  causal_names <- taxon_names[causal_idx]
  all_results$is_causal <- all_results$variable %in% causal_names

  # Summarize: for each model, how many causal found, how many FP at FDR < threshold
  summary_list <- list()
  for (m in unique(all_results$model)) {
    sub <- all_results[all_results$model == m, ]
    sig <- sub[sub$fdr < fdr_threshold, ]
    tp <- sum(sig$variable %in% causal_names)
    fp <- sum(!(sig$variable %in% causal_names))
    total_sig <- nrow(sig)
    fdr_actual <- ifelse(total_sig > 0, fp / total_sig, 0)
    summary_list[[m]] <- data.frame(
      model = m, sensitivity = tp / length(causal_names),
      n_significant = total_sig, true_positives = tp, false_positives = fp,
      observed_fdr = fdr_actual, stringsAsFactors = FALSE
    )
  }
  summary_df <- do.call(rbind, summary_list)
  rownames(summary_df) <- NULL

  cat("\n--- Model Comparison at FDR <", fdr_threshold, "---\n")
  print(summary_df, digits = 3, row.names = FALSE)

  #--- Plot 1: Side-by-side -log10(FDR) for causal taxa across models ---
  causal_results <- all_results[all_results$is_causal, ]
  causal_results$neglog10fdr <- -log10(causal_results$fdr)
  causal_results$neglog10fdr <- pmin(causal_results$neglog10fdr, 50)  # cap for display

  p1 <- ggplot(causal_results, aes(x = variable, y = neglog10fdr, fill = model)) +
    geom_col(position = "dodge") +
    geom_hline(yintercept = -log10(fdr_threshold), linetype = "dashed",
               color = "red") +
    annotate("text", x = 0.5, y = -log10(fdr_threshold) + 1,
             label = paste0("FDR = ", fdr_threshold), hjust = 0,
             color = "red", size = 3) +
    scale_fill_brewer(palette = "Set2") +
    labs(title = "Significance of Causal Taxa Across Models",
         subtitle = paste0("-log10(BH-adjusted p-value); dashed line = FDR ", fdr_threshold),
         x = "Causal Taxon", y = "-log10(FDR)", fill = "Model") +
    theme_minimal() +
    theme(legend.position = "bottom", axis.text.x = element_text(angle = 45, hjust = 1))
  ggsave("mixed_causal_significance.png", p1, width = 10, height = 6)

  #--- Plot 2: Summary bar chart (TP, FP per model) ---
  summary_long <- do.call(rbind, lapply(1:nrow(summary_df), function(i) {
    rbind(
      data.frame(model = summary_df$model[i], count = summary_df$true_positives[i],
                 type = "True Positives"),
      data.frame(model = summary_df$model[i], count = summary_df$false_positives[i],
                 type = "False Positives")
    )
  }))

  p2 <- ggplot(summary_long, aes(x = model, y = count, fill = type)) +
    geom_col(position = "dodge") +
    scale_fill_manual(values = c("True Positives" = "firebrick",
                                 "False Positives" = "grey60")) +
    labs(title = paste0("True vs False Positives at FDR < ", fdr_threshold),
         x = "", y = "Number of Taxa", fill = "") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1),
          legend.position = "bottom")
  ggsave("mixed_tp_fp_comparison.png", p2, width = 9, height = 6)

  #--- Plot 3: Volcano plot faceted by model ---
  all_results$neglog10p <- -log10(all_results$p_value)
  all_results$neglog10p <- pmin(all_results$neglog10p, 60)  # cap extreme values
  all_results$significant <- all_results$fdr < fdr_threshold

  p3 <- ggplot(all_results, aes(x = coefficient, y = neglog10p,
                                 color = is_causal, shape = significant)) +
    geom_point(size = 1.8, alpha = 0.7) +
    facet_wrap(~ model, scales = "free") +
    scale_color_manual(values = c("FALSE" = "grey50", "TRUE" = "firebrick"),
                       labels = c("Non-causal", "Causal")) +
    scale_shape_manual(values = c("TRUE" = 17, "FALSE" = 1)) +
    geom_hline(yintercept = -log10(0.05), linetype = "dashed", color = "grey70") +
    labs(title = "Volcano Plots: Four Modeling Approaches",
         x = "Coefficient", y = "-log10(p-value)",
         color = "True Status", shape = paste0("FDR < ", fdr_threshold)) +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave("mixed_volcano_comparison.png", p3, width = 12, height = 8)

  #--- Plot 4: FDR vs number of discoveries (across thresholds) ---
  thresholds <- c(0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50)
  fdr_curve <- do.call(rbind, lapply(unique(all_results$model), function(m) {
    sub <- all_results[all_results$model == m, ]
    do.call(rbind, lapply(thresholds, function(th) {
      sig <- sub[sub$fdr < th, ]
      tp <- sum(sig$variable %in% causal_names)
      fp <- sum(!(sig$variable %in% causal_names))
      data.frame(model = m, threshold = th, tp = tp, fp = fp,
                 n_sig = nrow(sig),
                 observed_fdr = ifelse(nrow(sig) > 0, fp / nrow(sig), 0))
    }))
  }))

  p4 <- ggplot(fdr_curve, aes(x = threshold, color = model)) +
    geom_line(aes(y = tp), linewidth = 1) +
    geom_point(aes(y = tp), size = 2) +
    geom_hline(yintercept = 5, linetype = "dotted", color = "black") +
    annotate("text", x = 0.45, y = 5.2, label = "5 true causal taxa", size = 3) +
    scale_color_brewer(palette = "Set2") +
    labs(title = "Causal Taxa Detected vs. FDR Threshold",
         x = "BH FDR Threshold", y = "Causal Taxa Detected (out of 5)",
         color = "Model") +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave("mixed_sensitivity_vs_threshold.png", p4, width = 10, height = 6)

  p5 <- ggplot(fdr_curve, aes(x = threshold, color = model)) +
    geom_line(aes(y = fp), linewidth = 1) +
    geom_point(aes(y = fp), size = 2) +
    scale_color_brewer(palette = "Set2") +
    labs(title = "False Positives vs. FDR Threshold",
         x = "BH FDR Threshold", y = "False Positives",
         color = "Model") +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave("mixed_fp_vs_threshold.png", p5, width = 10, height = 6)

  cat("Saved: mixed_causal_significance.png, mixed_tp_fp_comparison.png,\n")
  cat("       mixed_volcano_comparison.png, mixed_sensitivity_vs_threshold.png,\n")
  cat("       mixed_fp_vs_threshold.png\n")

  return(summary_df)
}

###############################################################################
# RUN ALL FOUR MODELS
###############################################################################

cat("================================================================\n")
cat("  Mixed-Effects Model Comparison\n")
cat("================================================================\n\n")

cat("--- Generating simulated data ---\n")
df <- simulate_study(
  n_households   = 20,
  n_persons_per  = 3,
  n_days         = 90,
  causal_effects = c(0.10, 0.08, 0.06, 0.04, 0.02),
  verbose        = TRUE
)

taxon_names  <- attr(df, "taxon_names")
causal_idx   <- attr(df, "causal_idx")
causal_names <- taxon_names[causal_idx]

cat("\n--- Model 1: Simple univariate (demeaned) ---\n")
res1 <- fit_simple_univariate(df, taxon_names)
sig1 <- res1[res1$fdr < 0.05, ]
cat(sprintf("  %d taxa significant at FDR < 0.05 (%d causal)\n",
            nrow(sig1), sum(sig1$variable %in% causal_names)))

cat("\n--- Model 2: Univariate + environmental covariates (demeaned) ---\n")
res2 <- fit_covariate_adjusted(df, taxon_names)
sig2 <- res2[res2$fdr < 0.05, ]
cat(sprintf("  %d taxa significant at FDR < 0.05 (%d causal)\n",
            nrow(sig2), sum(sig2$variable %in% causal_names)))

cat("\n--- Model 3: Mixed-effects (random intercepts, no covariates) ---\n")
res3 <- fit_mixed_effects(df, taxon_names)
sig3 <- res3[res3$fdr < 0.05, ]
cat(sprintf("  %d taxa significant at FDR < 0.05 (%d causal)\n",
            nrow(sig3), sum(sig3$variable %in% causal_names)))

cat("\n--- Model 4: Mixed-effects + environmental covariates ---\n")
res4 <- fit_mixed_effects_adjusted(df, taxon_names)
sig4 <- res4[res4$fdr < 0.05, ]
cat(sprintf("  %d taxa significant at FDR < 0.05 (%d causal)\n",
            nrow(sig4), sum(sig4$variable %in% causal_names)))

# Combine and compare
all_results <- rbind(res1, res2, res3, res4)

cat("\n--- Detailed results for causal taxa ---\n")
for (m in unique(all_results$model)) {
  cat(sprintf("\n  %s:\n", m))
  sub <- all_results[all_results$model == m & all_results$variable %in% causal_names, ]
  sub <- sub[order(sub$p_value), ]
  for (i in 1:nrow(sub)) {
    cat(sprintf("    %s: coef=%.4f, p=%.2e, fdr=%.2e %s\n",
                sub$variable[i], sub$coefficient[i], sub$p_value[i], sub$fdr[i],
                ifelse(sub$fdr[i] < 0.05, "*", "")))
  }
}

cat("\n--- Plotting model comparison ---\n")
summary_df <- plot_model_comparison(all_results, causal_idx, taxon_names)

# Save results
write.csv(all_results, "mixed_effects_results.csv", row.names = FALSE)
cat("\nSaved mixed_effects_results.csv\n")

cat("\n================================================================\n")
cat("  Done!\n")
cat("================================================================\n")
