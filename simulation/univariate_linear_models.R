###############################################################################
# Univariate Linear Models: Per-taxon association with allergy
#
# For each of 100 taxa, fit:
#   allergy_demeaned ~ taxon_demeaned
# Get p-values, apply BH FDR correction, compare to elastic net results.
###############################################################################

library(MASS)
library(glmnet)
library(ggplot2)

set.seed(42)

# Source the simulation function from the main script
# (parse only the function definitions, not the execution block)
source_lines <- readLines("sim_microbiome_allergies.R")
part6_line <- grep("PART 6: RUN EVERYTHING", source_lines)
tmp <- tempfile(fileext = ".R")
writeLines(source_lines[1:(part6_line - 1)], tmp)
source(tmp)

###############################################################################
# FIT UNIVARIATE LINEAR MODELS WITH PERSON DEMEANING
###############################################################################

fit_univariate_models <- function(df, taxon_names) {

  env_vars <- c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  all_vars <- c(taxon_names, env_vars)

  # Person-level demeaning
  df_dm <- df
  for (v in c("allergy", all_vars)) {
    pm <- tapply(df[[v]], df$person_id, mean)
    df_dm[[v]] <- df[[v]] - pm[as.character(df$person_id)]
  }

  # Fit one linear model per predictor
  results <- data.frame(
    variable    = character(0),
    coefficient = numeric(0),
    std_error   = numeric(0),
    t_value     = numeric(0),
    p_value     = numeric(0),
    r_squared   = numeric(0)
  )

  for (v in all_vars) {
    mod <- lm(allergy ~ x, data = data.frame(allergy = df_dm$allergy, x = df_dm[[v]]))
    s <- summary(mod)
    coef_row <- s$coefficients["x", ]
    results <- rbind(results, data.frame(
      variable    = v,
      coefficient = coef_row["Estimate"],
      std_error   = coef_row["Std. Error"],
      t_value     = coef_row["t value"],
      p_value     = coef_row["Pr(>|t|)"],
      r_squared   = s$r.squared,
      stringsAsFactors = FALSE
    ))
  }

  # BH FDR correction
  results$fdr <- p.adjust(results$p_value, method = "BH")

  # Sort by p-value
  results <- results[order(results$p_value), ]
  rownames(results) <- NULL

  return(results)
}

###############################################################################
# PLOT RESULTS
###############################################################################

plot_univariate_results <- function(results, causal_idx, taxon_names,
                                    fdr_threshold = 0.05) {

  causal_names <- taxon_names[causal_idx]

  # Mark causal status
  results$is_causal <- results$variable %in% causal_names
  results$is_env    <- results$variable %in%
                       c("temperature", "humidity", "pm25", "co2", "fungal_conc")
  results$var_type  <- ifelse(results$is_causal, "Causal taxon",
                       ifelse(results$is_env, "Environmental", "Non-causal taxon"))

  #--- Plot 1: Volcano plot (-log10 p-value vs coefficient) ---
  results$neglog10p <- -log10(results$p_value)
  results$significant <- results$fdr < fdr_threshold

  p1 <- ggplot(results, aes(x = coefficient, y = neglog10p,
                             color = var_type, shape = significant)) +
    geom_point(size = 2.5, alpha = 0.8) +
    scale_color_manual(values = c("Causal taxon" = "firebrick",
                                  "Non-causal taxon" = "grey50",
                                  "Environmental" = "steelblue")) +
    scale_shape_manual(values = c("TRUE" = 17, "FALSE" = 1)) +
    geom_hline(yintercept = -log10(0.05), linetype = "dashed", color = "grey70") +
    annotate("text", x = max(results$coefficient) * 0.8,
             y = -log10(0.05) + 0.3, label = "p = 0.05", color = "grey50", size = 3) +
    labs(title = "Volcano Plot: Univariate Linear Models (per taxon)",
         subtitle = paste0("Triangles = BH FDR < ", fdr_threshold),
         x = "Coefficient (demeaned allergy ~ demeaned taxon)",
         y = "-log10(p-value)",
         color = "Variable Type", shape = paste0("FDR < ", fdr_threshold)) +
    theme_minimal() +
    theme(legend.position = "bottom")
  ggsave("univariate_volcano.png", p1, width = 10, height = 7)

  #--- Plot 2: FDR-corrected p-values ranked ---
  # Show only taxa (not environmental)
  taxa_results <- results[!results$is_env, ]
  taxa_results$rank <- 1:nrow(taxa_results)

  p2 <- ggplot(taxa_results, aes(x = rank, y = -log10(fdr),
                                  color = is_causal)) +
    geom_point(size = 2) +
    scale_color_manual(values = c("FALSE" = "grey50", "TRUE" = "firebrick"),
                       labels = c("Non-causal", "Causal")) +
    geom_hline(yintercept = -log10(fdr_threshold), linetype = "dashed",
               color = "blue") +
    annotate("text", x = nrow(taxa_results) * 0.8,
             y = -log10(fdr_threshold) + 0.2,
             label = paste0("FDR = ", fdr_threshold), color = "blue", size = 3) +
    labs(title = "Taxa Ranked by BH-Corrected P-value",
         x = "Rank", y = "-log10(FDR-adjusted p-value)",
         color = "True Status") +
    theme_minimal()
  ggsave("univariate_fdr_ranked.png", p2, width = 10, height = 6)

  #--- Plot 3: Coefficient comparison (causal vs non-causal) ---
  taxa_results$label <- ifelse(taxa_results$is_causal, taxa_results$variable, "")
  top_n <- head(taxa_results, 20)
  top_n$variable <- factor(top_n$variable, levels = rev(top_n$variable))

  p3 <- ggplot(top_n, aes(x = coefficient, y = variable, fill = is_causal)) +
    geom_col() +
    scale_fill_manual(values = c("FALSE" = "grey60", "TRUE" = "firebrick"),
                      labels = c("Non-causal", "Causal"), name = "True Status") +
    geom_vline(xintercept = 0, linetype = "dashed") +
    labs(title = "Top 20 Taxa by P-value (Univariate Linear Models)",
         x = "Coefficient", y = "") +
    theme_minimal()
  ggsave("univariate_top20_coefficients.png", p3, width = 8, height = 6)

  cat("Saved: univariate_volcano.png, univariate_fdr_ranked.png, univariate_top20_coefficients.png\n")
}

###############################################################################
# RUN SINGLE ANALYSIS
###############################################################################

cat("================================================================\n")
cat("  Univariate Linear Models — Per-Taxon Analysis\n")
cat("================================================================\n\n")

cat("--- Generating simulated data ---\n")
df <- simulate_study(
  n_households   = 20,
  n_persons_per  = 3,
  n_days         = 90,
  causal_effects = c(0.10, 0.08, 0.06, 0.04, 0.02),
  verbose        = TRUE
)

taxon_names <- attr(df, "taxon_names")
causal_idx  <- attr(df, "causal_idx")
causal_names <- taxon_names[causal_idx]

cat("\n--- Fitting univariate linear models ---\n")
results <- fit_univariate_models(df, taxon_names)

# Summary
cat("\n--- Top 20 associations (by p-value) ---\n")
top20 <- head(results, 20)
top20$is_causal <- top20$variable %in% causal_names
print(top20[, c("variable", "coefficient", "p_value", "fdr", "r_squared", "is_causal")],
      digits = 4, row.names = FALSE)

# Count causal taxa at different FDR thresholds
for (threshold in c(0.05, 0.10, 0.20)) {
  sig <- results[results$fdr < threshold, ]
  sig_taxa <- sig$variable[sig$variable %in% taxon_names]
  tp <- sum(sig_taxa %in% causal_names)
  fp <- sum(!(sig_taxa %in% causal_names))
  cat(sprintf("\nAt FDR < %.2f: %d taxa significant (%d causal, %d non-causal)\n",
              threshold, length(sig_taxa), tp, fp))
  if (tp > 0) {
    cat(sprintf("  Causal taxa found: %s\n",
                paste(sig_taxa[sig_taxa %in% causal_names], collapse = ", ")))
  }
  if (fp > 0) {
    cat(sprintf("  False positives: %s\n",
                paste(head(sig_taxa[!(sig_taxa %in% causal_names)], 10), collapse = ", ")))
  }
}

cat("\n--- Plotting ---\n")
plot_univariate_results(results, causal_idx, taxon_names)

# Save full results
write.csv(results, "univariate_results.csv", row.names = FALSE)
cat("\nSaved univariate_results.csv\n")

cat("\n================================================================\n")
cat("  Done!\n")
cat("================================================================\n")
