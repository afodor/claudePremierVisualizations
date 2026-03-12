###############################################################################
# Mediation Analysis: Separating direct taxon effects from environment-confounded
#
# For each taxon, decompose the total association with allergy into:
#   1. Direct path:    taxon -> allergy (adjusting for environment)
#   2. Confounded path: environment -> taxon AND environment -> allergy
#
# A truly causal taxon should retain its significance after adjusting for
# environmental covariates. A confounded taxon (e.g., humidity-linked) will
# lose significance because the association was driven by the shared
# environmental driver.
#
# Mediation approach (Baron & Kenny + Sobel):
#   Total effect (c):   allergy ~ taxon
#   Direct effect (c'): allergy ~ taxon + environment
#   a path:             taxon ~ environment
#   b path:             environment coefficient in allergy ~ taxon + environment
#   Indirect effect:    c - c'  (or equivalently, a * b)
#   Attenuation:        (c - c') / c
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
# Mediation decomposition for each taxon
###############################################################################

run_mediation <- function(df, taxon_names) {
  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  all_vars <- c(taxon_names, env_vars)

  # Person-level demeaning
  df_dm <- df
  for (v in c("allergy", all_vars)) {
    pm <- tapply(df[[v]], df$person_id, mean)
    df_dm[[v]] <- df[[v]] - pm[as.character(df$person_id)]
  }

  results <- list()
  for (i in seq_along(taxon_names)) {
    v <- taxon_names[i]

    # --- Total effect (c path): allergy ~ taxon ---
    mod_total <- lm(allergy ~ x, data = data.frame(allergy = df_dm$allergy, x = df_dm[[v]]))
    s_total <- summary(mod_total)
    coef_total <- s_total$coefficients["x", "Estimate"]
    p_total <- s_total$coefficients["x", "Pr(>|t|)"]

    # --- Direct effect (c' path): allergy ~ taxon + environment ---
    mod_df <- data.frame(
      allergy = df_dm$allergy, taxon = df_dm[[v]],
      temperature = df_dm$temperature, humidity = df_dm$humidity,
      pm25 = df_dm$pm25, co2 = df_dm$co2, fungal_conc = df_dm$fungal_conc
    )
    mod_direct <- lm(allergy ~ taxon + temperature + humidity + pm25 + co2 + fungal_conc,
                     data = mod_df)
    s_direct <- summary(mod_direct)
    coef_direct <- s_direct$coefficients["taxon", "Estimate"]
    p_direct <- s_direct$coefficients["taxon", "Pr(>|t|)"]

    # --- a path: taxon ~ environment (how strongly is taxon driven by env?) ---
    mod_a <- lm(taxon ~ temperature + humidity + pm25 + co2 + fungal_conc, data = mod_df)
    s_a <- summary(mod_a)
    r2_env <- s_a$r.squared  # how much env explains this taxon
    f_stat <- s_a$fstatistic
    p_env <- pf(f_stat[1], f_stat[2], f_stat[3], lower.tail = FALSE)

    # --- Indirect effect and attenuation ---
    indirect <- coef_total - coef_direct
    attenuation <- ifelse(abs(coef_total) > 1e-10, indirect / coef_total, 0)

    # --- Sobel test for indirect effect ---
    # SE of indirect effect (approximate): sqrt(a^2 * se_b^2 + b^2 * se_a^2)
    # For simplicity, use the difference method with bootstrap-like SE
    se_total <- s_total$coefficients["x", "Std. Error"]
    se_direct <- s_direct$coefficients["taxon", "Std. Error"]
    # Approximate SE of indirect effect
    se_indirect <- sqrt(se_total^2 + se_direct^2)
    z_indirect <- indirect / se_indirect
    p_indirect <- 2 * pnorm(abs(z_indirect), lower.tail = FALSE)

    results[[i]] <- data.frame(
      variable = v,
      coef_total = coef_total,
      p_total = p_total,
      coef_direct = coef_direct,
      p_direct = p_direct,
      indirect_effect = indirect,
      p_indirect = p_indirect,
      attenuation = attenuation,
      env_r2 = r2_env,
      p_env = p_env,
      stringsAsFactors = FALSE
    )
  }

  out <- do.call(rbind, results)
  out$fdr_total <- p.adjust(out$p_total, method = "BH")
  out$fdr_direct <- p.adjust(out$p_direct, method = "BH")
  out$fdr_env <- p.adjust(out$p_env, method = "BH")
  rownames(out) <- NULL
  return(out)
}

###############################################################################
# Classification: direct, confounded, or null
###############################################################################

classify_taxa <- function(med_results, fdr_thresh = 0.05, attenuation_thresh = 0.50) {
  med_results$class <- "Null"

  # Significant total effect AND significant direct effect AND low attenuation
  # -> likely direct causal effect
  direct <- med_results$fdr_total < fdr_thresh &
            med_results$fdr_direct < fdr_thresh &
            abs(med_results$attenuation) < attenuation_thresh
  med_results$class[direct] <- "Direct"

  # Significant total effect BUT loses significance or high attenuation
  # -> likely confounded through environment
  confounded <- med_results$fdr_total < fdr_thresh &
                (med_results$fdr_direct >= fdr_thresh | abs(med_results$attenuation) >= attenuation_thresh)
  med_results$class[confounded] <- "Confounded"

  # Additionally flag taxa strongly driven by environment
  med_results$env_driven <- med_results$fdr_env < fdr_thresh & med_results$env_r2 > 0.01

  return(med_results)
}

###############################################################################
# Power analysis: does mediation reduce FP with larger samples?
###############################################################################

cat("================================================================\n")
cat("  Mediation Analysis: Direct vs Confounded Taxon Effects\n")
cat("================================================================\n\n")

n_sims <- 50
households_vec <- c(5, 10, 20, 40, 80, 160)
base_effects <- c(0.10, 0.08, 0.06, 0.04, 0.02)

results_power <- data.frame()

cat("=== Power analysis: mediation classification across sample sizes ===\n")
for (nh in households_vec) {
  for (sim in 1:n_sims) {
    df <- simulate_study(n_households = nh, n_persons_per = 3, n_days = 90,
                         causal_effects = base_effects)
    tn <- attr(df, "taxon_names")
    ci <- attr(df, "causal_idx")
    cn <- tn[ci]

    med <- run_mediation(df, tn)
    med <- classify_taxa(med)

    # --- Standard approach: univariate BH FDR ---
    sig_standard <- med[med$fdr_total < 0.05, ]
    tp_standard <- sum(sig_standard$variable %in% cn)
    fp_standard <- sum(!(sig_standard$variable %in% cn))

    # --- Covariate-adjusted: BH FDR on direct effect ---
    sig_adjusted <- med[med$fdr_direct < 0.05, ]
    tp_adjusted <- sum(sig_adjusted$variable %in% cn)
    fp_adjusted <- sum(!(sig_adjusted$variable %in% cn))

    # --- Mediation approach: only "Direct" class taxa ---
    sig_mediation <- med[med$class == "Direct", ]
    tp_mediation <- sum(sig_mediation$variable %in% cn)
    fp_mediation <- sum(!(sig_mediation$variable %in% cn))

    # --- Strict mediation: direct class + not env-driven ---
    sig_strict <- med[med$class == "Direct" & !med$env_driven, ]
    tp_strict <- sum(sig_strict$variable %in% cn)
    fp_strict <- sum(!(sig_strict$variable %in% cn))

    for (method_info in list(
      list("Standard (total FDR<0.05)", tp_standard, fp_standard, nrow(sig_standard)),
      list("Adjusted (direct FDR<0.05)", tp_adjusted, fp_adjusted, nrow(sig_adjusted)),
      list("Mediation (Direct class)", tp_mediation, fp_mediation, nrow(sig_mediation)),
      list("Strict mediation", tp_strict, fp_strict, nrow(sig_strict))
    )) {
      tp <- method_info[[2]]; fp <- method_info[[3]]; ns <- method_info[[4]]
      results_power <- rbind(results_power, data.frame(
        households = nh, sim = sim, method = method_info[[1]],
        sensitivity = tp / length(cn),
        false_positives = fp,
        n_significant = ns,
        observed_fdr = ifelse(ns > 0, fp / ns, 0)
      ))
    }
  }
  cat(sprintf("  households=%d done\n", nh))
}

###############################################################################
# Summarize and plot
###############################################################################

agg <- aggregate(
  cbind(sensitivity, false_positives, observed_fdr) ~ households + method,
  data = results_power, FUN = mean
)
agg_se <- aggregate(
  cbind(sensitivity, false_positives, observed_fdr) ~ households + method,
  data = results_power, FUN = function(x) sd(x) / sqrt(length(x))
)
names(agg_se)[3:5] <- paste0(names(agg_se)[3:5], "_se")
plotdata <- merge(agg, agg_se)

# Order methods logically
plotdata$method <- factor(plotdata$method, levels = c(
  "Standard (total FDR<0.05)", "Adjusted (direct FDR<0.05)",
  "Mediation (Direct class)", "Strict mediation"
))

# --- Plot 1: Sensitivity ---
p1 <- ggplot(plotdata, aes(x = households, y = sensitivity, color = method)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, sensitivity - 1.96 * sensitivity_se),
                    ymax = pmin(1, sensitivity + 1.96 * sensitivity_se)),
                width = 0) +
  geom_hline(yintercept = 0.8, linetype = "dashed", color = "grey50") +
  scale_color_brewer(palette = "Set1") +
  ylim(0, 1) +
  labs(title = "Sensitivity: Standard vs Mediation Approaches",
       x = "Number of Households", y = "Sensitivity (causal taxa detected / 5)",
       color = "Method") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("mediation_sensitivity.png", p1, width = 11, height = 6)

# --- Plot 2: False positives ---
p2 <- ggplot(plotdata, aes(x = households, y = false_positives, color = method)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, false_positives - 1.96 * false_positives_se),
                    ymax = false_positives + 1.96 * false_positives_se),
                width = 0) +
  scale_color_brewer(palette = "Set1") +
  labs(title = "False Positives: Standard vs Mediation Approaches",
       x = "Number of Households", y = "False Positives (out of 95 non-causal)",
       color = "Method") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("mediation_false_positives.png", p2, width = 11, height = 6)

# --- Plot 3: Observed FDR ---
p3 <- ggplot(plotdata, aes(x = households, y = observed_fdr, color = method)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, observed_fdr - 1.96 * observed_fdr_se),
                    ymax = pmin(1, observed_fdr + 1.96 * observed_fdr_se)),
                width = 0) +
  geom_hline(yintercept = 0.05, linetype = "dashed", color = "red") +
  scale_color_brewer(palette = "Set1") +
  ylim(0, 1) +
  labs(title = "Observed FDR: Standard vs Mediation Approaches",
       subtitle = "Can mediation bring FDR closer to the nominal 5%?",
       x = "Number of Households", y = "Observed FDR",
       color = "Method") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("mediation_observed_fdr.png", p3, width = 11, height = 6)

# --- Plot 4: Sensitivity vs FDR tradeoff ---
p4 <- ggplot(plotdata, aes(x = observed_fdr, y = sensitivity,
                            color = method, label = households)) +
  geom_path(linewidth = 1, arrow = arrow(length = unit(0.15, "inches"))) +
  geom_point(size = 3) +
  geom_text(aes(label = households), vjust = -1, size = 3) +
  geom_hline(yintercept = 0.8, linetype = "dashed", color = "grey50") +
  geom_vline(xintercept = 0.05, linetype = "dashed", color = "red") +
  scale_color_brewer(palette = "Set1") +
  xlim(0, 1) + ylim(0, 1) +
  labs(title = "Sensitivity vs Observed FDR (numbers = households)",
       subtitle = "Ideal = top-left corner (high sensitivity, low FDR)",
       x = "Observed FDR", y = "Sensitivity",
       color = "Method") +
  theme_minimal() + theme(legend.position = "bottom")
ggsave("mediation_tradeoff.png", p4, width = 10, height = 8)

write.csv(results_power, "mediation_power_results.csv", row.names = FALSE)

###############################################################################
# Single-run detailed example (20 HH, 90 days)
###############################################################################

cat("\n=== Detailed single-run example (20 HH x 3 persons x 90 days) ===\n\n")
df <- simulate_study(n_households = 20, n_persons_per = 3, n_days = 90,
                     causal_effects = base_effects, verbose = TRUE)
tn <- attr(df, "taxon_names")
ci <- attr(df, "causal_idx")
cn <- tn[ci]

med <- run_mediation(df, tn)
med <- classify_taxa(med)

# Print causal taxa
cat("\n--- Causal taxa mediation results ---\n")
causal_med <- med[med$variable %in% cn, ]
causal_med <- causal_med[order(causal_med$p_total), ]
cat(sprintf("%-12s %8s %8s %8s %10s %6s %8s %s\n",
            "Taxon", "CoefTot", "CoefDir", "Atten%", "EnvR2", "Class", "FDR_dir", "EnvDriven"))
for (i in 1:nrow(causal_med)) {
  r <- causal_med[i, ]
  cat(sprintf("%-12s %8.4f %8.4f %7.1f%% %9.4f %6s %8.2e %s\n",
              r$variable, r$coef_total, r$coef_direct,
              100 * r$attenuation, r$env_r2, r$class,
              r$fdr_direct, ifelse(r$env_driven, "YES", "no")))
}

# Print top false positives from standard approach
cat("\n--- Top false positives (significant total, non-causal) ---\n")
fp_taxa <- med[med$fdr_total < 0.05 & !(med$variable %in% cn), ]
fp_taxa <- fp_taxa[order(fp_taxa$p_total), ]
if (nrow(fp_taxa) > 0) {
  cat(sprintf("%-12s %8s %8s %8s %10s %6s %8s %s\n",
              "Taxon", "CoefTot", "CoefDir", "Atten%", "EnvR2", "Class", "FDR_dir", "EnvDriven"))
  for (i in 1:min(15, nrow(fp_taxa))) {
    r <- fp_taxa[i, ]
    cat(sprintf("%-12s %8.4f %8.4f %7.1f%% %9.4f %6s %8.2e %s\n",
                r$variable, r$coef_total, r$coef_direct,
                100 * r$attenuation, r$env_r2, r$class,
                r$fdr_direct, ifelse(r$env_driven, "YES", "no")))
  }
} else {
  cat("  (none)\n")
}

# Summary comparison
cat("\n--- Classification summary ---\n")
cat(sprintf("  Direct class:     %d taxa (%d causal, %d FP)\n",
            sum(med$class == "Direct"),
            sum(med$class == "Direct" & med$variable %in% cn),
            sum(med$class == "Direct" & !(med$variable %in% cn))))
cat(sprintf("  Confounded class: %d taxa (%d causal, %d FP)\n",
            sum(med$class == "Confounded"),
            sum(med$class == "Confounded" & med$variable %in% cn),
            sum(med$class == "Confounded" & !(med$variable %in% cn))))
cat(sprintf("  Null class:       %d taxa\n", sum(med$class == "Null")))

# Known env-linked non-causal taxa in simulation
known_confounded <- c("taxon_010", "taxon_015", "taxon_020",  # humidity-linked
                      "taxon_011", "taxon_016", "taxon_025",  # temp-linked
                      "taxon_012", "taxon_017", "taxon_030", "taxon_035")  # PM2.5-linked
cat("\n--- Known environment-linked non-causal taxa ---\n")
known_med <- med[med$variable %in% known_confounded, ]
known_med <- known_med[order(known_med$p_total), ]
cat(sprintf("%-12s %8s %8s %8s %10s %6s %8s %s\n",
            "Taxon", "CoefTot", "CoefDir", "Atten%", "EnvR2", "Class", "FDR_tot", "EnvDriven"))
for (i in 1:nrow(known_med)) {
  r <- known_med[i, ]
  cat(sprintf("%-12s %8.4f %8.4f %7.1f%% %9.4f %6s %8.2e %s\n",
              r$variable, r$coef_total, r$coef_direct,
              100 * r$attenuation, r$env_r2, r$class,
              r$fdr_total, ifelse(r$env_driven, "YES", "no")))
}

cat("\n================================================================\n")
cat("  Summary of power analysis saved to mediation_power_results.csv\n")
cat("  Plots: mediation_sensitivity.png, mediation_false_positives.png,\n")
cat("         mediation_observed_fdr.png, mediation_tradeoff.png\n")
cat("================================================================\n")

# Print power summary table
cat("\n--- Power summary: Mediation vs Standard (mean across 50 sims) ---\n")
cat(sprintf("%-30s %4s %6s %4s %6s\n", "Method", "HH", "Sens", "FP", "FDR"))
for (i in 1:nrow(plotdata)) {
  r <- plotdata[i, ]
  cat(sprintf("%-30s %4d %5.2f %5.1f %5.3f\n",
              as.character(r$method), r$households,
              r$sensitivity, r$false_positives, r$observed_fdr))
}
