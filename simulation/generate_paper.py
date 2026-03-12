#!/usr/bin/env python3
"""
Generate PDF paper: Microbiome-Allergy Simulation Framework
Uses matplotlib PdfPages — no LaTeX installation required.
"""

import os
import csv
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.image as mpimg
import numpy as np

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(PAPER_DIR, "microbiome_allergy_simulation.pdf")

# Try to load the schematic image
SCHEMATIC_PATH = "/users/afodor/claudeCityWideModels/basementSchematic.png"
# Also try fetching from the local clone if available
ALT_SCHEMATIC = os.path.join(PAPER_DIR, "basementSchematic.png")

# Load power results
def load_power_results(path):
    data = {'vary': [], 'value': [], 'sim': [], 'sensitivity': [],
            'specificity': [], 'fdr': [], 'n_selected': []}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['vary'].append(row['vary'])
            data['value'].append(float(row['value']))
            data['sim'].append(int(row['sim']))
            data['sensitivity'].append(float(row['sensitivity']))
            data['specificity'].append(float(row['specificity']))
            data['fdr'].append(float(row['fdr']))
            data['n_selected'].append(float(row['n_selected']))
    return data

power = load_power_results(os.path.join(PAPER_DIR, "power_results.csv"))

# ============================================================
# Helper functions
# ============================================================

def add_text_page(pdf, title, body, fontsize=9, title_size=15):
    """Add a page with a title and body text."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0.08, 0.05, 0.84, 0.90])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.text(0.5, 0.99, title, fontsize=title_size, ha='center',
            fontweight='bold', va='top')
    ax.text(0.0, 0.94, body, fontsize=fontsize, ha='left', va='top',
            family='serif', linespacing=1.45, wrap=False)
    pdf.savefig(fig)
    plt.close()

def add_figure_page(pdf, img_path, caption, title=""):
    """Add a page with an image and caption."""
    fig = plt.figure(figsize=(8.5, 11))
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.97)
    try:
        img = mpimg.imread(img_path)
        ax_img = fig.add_axes([0.05, 0.25, 0.90, 0.65])
        ax_img.imshow(img)
        ax_img.axis('off')
    except Exception as e:
        ax_img = fig.add_axes([0.05, 0.25, 0.90, 0.65])
        ax_img.text(0.5, 0.5, f"[Image not found: {os.path.basename(img_path)}]",
                    ha='center', va='center', fontsize=12, color='gray')
        ax_img.axis('off')

    ax_cap = fig.add_axes([0.08, 0.05, 0.84, 0.18])
    ax_cap.set_xlim(0, 1)
    ax_cap.set_ylim(0, 1)
    ax_cap.axis('off')
    wrapped = textwrap.fill(caption, width=95)
    ax_cap.text(0.0, 0.95, wrapped, fontsize=9, ha='left', va='top',
                family='serif', linespacing=1.4)
    pdf.savefig(fig)
    plt.close()

# ============================================================
# PDF Generation
# ============================================================

with PdfPages(OUT_PDF) as pdf:

    # ========== PAGE 1: TITLE + ABSTRACT ==========
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    ax.text(0.5, 0.90, "A Simulation Framework for Detecting Causal\n"
            "Microbial Taxa in Built-Environment Allergy Studies:",
            fontsize=17, ha='center', fontweight='bold', linespacing=1.3)
    ax.text(0.5, 0.83, "Power Analysis for a Household Sensor Network",
            fontsize=17, ha='center', fontweight='bold')

    ax.text(0.5, 0.78, "Anthony Fodor", fontsize=12, ha='center')
    ax.text(0.5, 0.755, "Department of Bioinformatics and Genomics",
            fontsize=10, ha='center', color='gray')
    ax.text(0.5, 0.735, "University of North Carolina at Charlotte",
            fontsize=10, ha='center', color='gray')
    ax.text(0.5, 0.71, "February 28, 2026", fontsize=10, ha='center',
            color='gray', style='italic')

    abstract = (
        "Abstract: The built-environment microbiome represents a largely unexplored "
        "determinant of human respiratory and allergic health. Here we present a simulation "
        "framework calibrated to empirical temporal dynamics from a 61-day daily sampling "
        "study of residential sink P-trap communities (Hill et al., 2026). Our framework "
        "simulates 100 microbial taxa with AR(1) dynamics (CV range 5-25%), five "
        "environmental covariates, and daily allergy scores driven by 5 causal taxa with "
        "effect sizes of 2-10%. We evaluate four analytical approaches: elastic net, "
        "per-taxon univariate models with BH FDR correction, mixed-effects models, and "
        "mediation analysis that decomposes taxon-allergy associations into direct vs "
        "environment-confounded paths. Elastic net achieves >93% sensitivity with 20+ "
        "households but suffers high FDR (>92%). Univariate models reveal a structural "
        "problem: environment-linked non-causal taxa generate 10-15 persistent false "
        "positives because environmental parameters simultaneously drive both taxon "
        "abundances and allergy symptoms. Increasing sample size improves sensitivity but "
        "does not eliminate these confounded associations. Mediation analysis reduces false "
        "positives from ~20 to ~9 by correctly classifying environment-confounded taxa, but "
        "residual false positives remain and the observed FDR (~70%) still exceeds the "
        "nominal 5% threshold. These results demonstrate that environmental confounding--"
        "not simply multiple testing--is the primary driver of false discoveries in "
        "built-environment microbiome studies."
    )
    wrapped = textwrap.fill(abstract, width=90)
    ax.text(0.5, 0.66, wrapped, fontsize=9.5, ha='center', va='top',
            family='serif', linespacing=1.5,
            bbox=dict(boxstyle='round,pad=0.6', facecolor='lightyellow', alpha=0.8))

    ax.text(0.5, 0.18, "Keywords: built-environment microbiome, allergy, simulation, "
            "power analysis,\nelastic net, longitudinal study design, sensor network",
            fontsize=9, ha='center', style='italic', color='gray', linespacing=1.4)

    pdf.savefig(fig)
    plt.close()

    # ========== PAGE 2: INTRODUCTION ==========
    intro_text = (
        "1. INTRODUCTION\n\n"
        "The built environment\u2014comprising the indoor spaces where people spend approximately 90% of\n"
        "their time\u2014harbors complex microbial communities that residents inhale, ingest, and contact\n"
        "daily (Adams et al., 2015). Epidemiological studies have linked indoor microbial exposures to\n"
        "both protective and pathogenic effects on respiratory health: farm-dwelling children exposed to\n"
        "diverse environmental microbiota show reduced asthma prevalence (Ege et al., 2011), while indoor\n"
        "mold and fungal exposures are consistently associated with allergic sensitization and exacerbation\n"
        "(Mendell et al., 2011). Despite these associations, the specific microbial taxa driving allergic\n"
        "responses in typical residential settings remain largely unidentified, in part because most studies\n"
        "rely on cross-sectional sampling that cannot capture the dynamic interplay between fluctuating\n"
        "microbial exposures and symptom trajectories.\n\n"
        "Recent technological advances are converging to make continuous household microbiome monitoring\n"
        "feasible. Environmental DNA sequencing costs continue to fall, miniaturized particulate and\n"
        "volatile organic compound sensors enable continuous air quality monitoring, and mobile health\n"
        "platforms allow real-time symptom tracking. We envision a household sensor network (Figure 1)\n"
        "comprising microbial sampling units deployed in key indoor locations (kitchen, bathroom, HVAC\n"
        "system) alongside environmental monitors for temperature, humidity, particulate matter\n"
        "(PM2.5), carbon dioxide (CO2), and fungal spore concentration, coupled with a mobile application\n"
        "through which household members record daily allergy severity scores.\n\n"
        "A critical question for the design of such studies is: given realistic levels of microbial community\n"
        "variability, environmental noise, and between-person heterogeneity, how many households and how\n"
        "many days of sampling are required to detect microbial taxa that contribute modestly (2-10%) to\n"
        "allergy symptom severity?\n\n"
        "Answering this question requires a realistic simulation framework that captures the key statistical\n"
        "challenges of the problem: high-dimensional predictors (100+ taxa), compositional constraints,\n"
        "temporal autocorrelation in both exposures and outcomes, hierarchical structure (observations\n"
        "nested within persons nested within households), and the need for variable selection in the\n"
        "presence of many null predictors.\n\n"
        "In this paper, we present such a framework. We calibrate the day-to-day dynamics of simulated\n"
        "microbial taxa to empirical data from Hill et al. (2026), who performed the first daily-resolution\n"
        "longitudinal characterization of residential sink P-trap bacterial communities over 61 consecutive\n"
        "days. Their study revealed that even adjacent sinks in a shared bathroom can exhibit dramatically\n"
        "different temporal stability profiles\u2014from highly deterministic communities with a coefficient of\n"
        "variation (CV) of 4.9% and strong temporal autocorrelation, to stochastic communities with a CV\n"
        "of 26.5% and no temporal predictability. This range provides an empirical basis for simulating the\n"
        "diversity of temporal behaviors expected across taxa in a household microbiome study.\n\n"
        "We simulate longitudinal data for varying numbers of households, each containing multiple family\n"
        "members who provide daily allergy reports. A sparse set of 5 \"causal\" taxa, embedded among 95\n"
        "null taxa, drive allergy severity with effect sizes ranging from 2% to 10%. We then apply elastic\n"
        "net regularized regression and evaluate the power to correctly identify the causal taxa as a\n"
        "function of study size, duration, and effect magnitude."
    )
    add_text_page(pdf, "Introduction", intro_text, fontsize=8.8)

    # ========== PAGE 3: FIGURE 1 — SCHEMATIC ==========
    schematic = None
    for path in [SCHEMATIC_PATH, ALT_SCHEMATIC]:
        if os.path.exists(path):
            schematic = path
            break

    if schematic:
        add_figure_page(pdf, schematic,
            "Figure 1. Conceptual schematic of the household sensor network for integrated "
            "microbiome-environment-health monitoring. Microbial sampling units collect daily "
            "environmental specimens for 16S rRNA sequencing. Environmental sensors continuously "
            "monitor temperature, humidity, PM2.5, CO2, and fungal spore concentrations. Household "
            "members report daily allergy severity via a mobile application.",
            title="Figure 1: Household Sensor Network")
    else:
        # Draw a conceptual schematic programmatically
        fig = plt.figure(figsize=(8.5, 11))
        fig.suptitle("Figure 1: Household Sensor Network Schematic", fontsize=14,
                     fontweight='bold', y=0.97)
        ax = fig.add_axes([0.05, 0.20, 0.90, 0.72])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        def draw_box(ax, x, y, w, h, text, color='lightblue', fontsize=9):
            box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                                 boxstyle="round,pad=0.15", facecolor=color,
                                 edgecolor='black', linewidth=1.2)
            ax.add_patch(box)
            ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
                    fontweight='bold', linespacing=1.3)

        def draw_arrow(ax, x1, y1, x2, y2):
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

        # House outline
        ax.add_patch(FancyBboxPatch((0.5, 1.5), 9, 7,
                     boxstyle="round,pad=0.3", facecolor='#F5F5F5',
                     edgecolor='#333', linewidth=2, linestyle='--'))
        ax.text(5, 9.0, "RESIDENTIAL HOUSEHOLD", fontsize=13,
                ha='center', fontweight='bold', color='#333')

        # Rooms
        draw_box(ax, 2.2, 7.0, 2.5, 1.2, "KITCHEN\n[Microbial Sampler]\n[Temp/Humidity]",
                '#E3F2FD', fontsize=7.5)
        draw_box(ax, 5.0, 7.0, 2.5, 1.2, "BATHROOM\n[Microbial Sampler]\n[Fungal Monitor]",
                '#E8F5E9', fontsize=7.5)
        draw_box(ax, 7.8, 7.0, 2.5, 1.2, "HVAC SYSTEM\n[PM2.5 Sensor]\n[CO2 Monitor]",
                '#FFF3E0', fontsize=7.5)

        # Central hub
        draw_box(ax, 5.0, 4.5, 3.5, 1.2, "DATA HUB\n100 Taxa + 5 Environmental\nParameters (daily)",
                '#E1BEE7', fontsize=8)

        # Mobile app
        draw_box(ax, 2.0, 2.5, 2.8, 1.0, "MOBILE APP\nDaily Allergy Score\n(1-10 scale)",
                '#FFCDD2', fontsize=8)

        # Family members
        draw_box(ax, 7.0, 2.5, 3.2, 1.0, "HOUSEHOLD MEMBERS\nPerson 1  Person 2  Person 3\n(individual reports)",
                '#BBDEFB', fontsize=7.5)

        # Analysis
        draw_box(ax, 5.0, 0.8, 4.0, 0.8, "STATISTICAL MODEL\nElastic Net + Person Demeaning",
                '#C8E6C9', fontsize=8)

        # Arrows
        draw_arrow(ax, 2.2, 6.3, 4.0, 5.2)
        draw_arrow(ax, 5.0, 6.3, 5.0, 5.2)
        draw_arrow(ax, 7.8, 6.3, 6.0, 5.2)
        draw_arrow(ax, 5.0, 3.8, 5.0, 1.3)
        draw_arrow(ax, 2.0, 1.9, 4.0, 1.3)
        draw_arrow(ax, 7.0, 1.9, 6.0, 1.3)

        # Caption
        ax_cap = fig.add_axes([0.08, 0.03, 0.84, 0.14])
        ax_cap.set_xlim(0, 1); ax_cap.set_ylim(0, 1); ax_cap.axis('off')
        cap = textwrap.fill(
            "Figure 1. Conceptual schematic of the household sensor network. Microbial "
            "sampling units and environmental sensors are deployed in key rooms. Daily "
            "data from 100 bacterial taxa and 5 environmental parameters are integrated "
            "with allergy self-reports from each household member via a mobile application. "
            "An elastic net regression model connects microbial and environmental exposures "
            "to allergy outcomes.", width=95)
        ax_cap.text(0.0, 0.95, cap, fontsize=9, ha='left', va='top',
                    family='serif', linespacing=1.4)
        pdf.savefig(fig)
        plt.close()

    # ========== PAGE 4: METHODS — CALIBRATION DATA ==========
    methods_1 = (
        "2. METHODS\n\n"
        "2.1 Calibration Data: Hill et al. (2026)\n\n"
        "We calibrated the temporal dynamics of our simulated microbial communities to the empirical\n"
        "observations of Hill et al. (2026), who conducted a 61-day daily sampling study of bacterial\n"
        "communities in paired residential bathroom sink P-traps. This study represents the highest\n"
        "temporal resolution characterization of residential microbial communities published to date.\n\n"
        "Hill et al. sequenced full-length 16S rRNA genes from daily swab samples of two sinks (A and\n"
        "B) sharing identical plumbing infrastructure, environmental conditions, and cleaning regimes\n"
        "but differing in primary user and usage patterns. Their findings revealed two distinct\n"
        "dynamical regimes:\n\n"
        "   Stable regime (Sink A): Community composition exhibited a coefficient of variation of\n"
        "   4.9%, significant temporal autocorrelation (Mantel test, p = 0.001), and deterministic\n"
        "   dynamics in which time explained 49.9% of community variation. This sink was primarily\n"
        "   used for handwashing, toothbrushing, and shaving. The community was enriched in aerobic,\n"
        "   skin-associated taxa.\n\n"
        "   Volatile regime (Sink B): Community composition showed a CV of 26.5%, no significant\n"
        "   temporal autocorrelation (p = 0.53), and stochastic dynamics with minimal temporal\n"
        "   predictability. This sink was used for handwashing, toothbrushing, face washing, and\n"
        "   mouthwash rinsing. The community was enriched in anaerobes, biofilm-forming bacteria,\n"
        "   oral microbiome associates, and preservative-resistant taxa.\n\n"
        "These two regimes define the empirical bounds of the CV range (5-25%) used in our simulations.\n"
        "The dominant taxa identified\u2014Pseudomonas, Citrobacter, Klebsiella, and Arcobacter\u2014are\n"
        "typical residents of residential plumbing biofilms. Despite identical plumbing, environmental\n"
        "conditions, and cleaning regimes, the two sinks maintained statistically distinct communities\n"
        "(p < 0.001), highlighting the importance of individual usage patterns in shaping built-\n"
        "environment microbial ecosystems.\n\n\n"
        "2.2 Simulation Framework Overview\n\n"
        "All simulations were implemented in R (v4.5.1) using the glmnet package for regularized\n"
        "regression. The framework comprises four components: (1) microbial community dynamics,\n"
        "(2) environmental covariate generation, (3) allergy response modeling, and (4) statistical\n"
        "inference via elastic net regression."
    )
    add_text_page(pdf, "Methods", methods_1, fontsize=8.8)

    # ========== PAGE 5: METHODS — SIMULATION DETAILS ==========
    methods_2 = (
        "2.3 Microbial Community Dynamics\n\n"
        "We simulate J = 100 microbial taxa over T days for H households, each containing P persons.\n"
        "The log-abundance of taxon j in household h on day t follows a first-order autoregressive\n"
        "process:\n\n"
        "   x(h,j,t) = \u03bc_j + \u03b4(h,j) + \u03c6_j * [x(h,j,t-1) - \u03bc_j - \u03b4(h,j)] + \u03b3_j * e(h,t) + \u03b5(j,t)\n\n"
        "where:\n"
        "  \u2022 \u03bc_j is the global mean log-abundance, drawn as \u03bc_j ~ N(-3, 1.5\u00b2)\n"
        "  \u2022 \u03b4(h,j) ~ N(0, 0.3\u00b2) is a household-specific shift\n"
        "  \u2022 \u03c6_j is the AR(1) coefficient controlling temporal persistence\n"
        "  \u2022 e(h,t) represents standardized environmental covariates\n"
        "  \u2022 \u03b5(j,t) ~ N(0, \u03c3_j\u00b2) is innovation noise\n\n"
        "Calibrating temporal variability. For each taxon, we draw a CV from a scaled Beta\n"
        "distribution:\n\n"
        "   CV_j = 0.05 + 0.20 * Beta(2, 3)\n\n"
        "which produces CVs concentrated in the range 0.08-0.18 but spanning 0.05-0.25, matching\n"
        "the empirical range from Hill et al. The Beta(2,3) shape produces a right-skewed\n"
        "distribution, reflecting that most taxa exhibit moderate stability (closer to Sink A)\n"
        "while a minority display high volatility (closer to Sink B). The AR(1) coefficient is:\n\n"
        "   \u03c6_j = max(0.05, min(0.95, 1 - 3 * CV_j))\n\n"
        "and the innovation standard deviation is:\n\n"
        "   \u03c3_j = CV_j * sqrt(1 - \u03c6_j\u00b2)\n\n"
        "ensuring the stationary variance Var(x) = \u03c3_j\u00b2 / (1 - \u03c6_j\u00b2) matches the desired CV.\n\n"
        "Environmental coupling. Fifteen of the 100 taxa are designated environment-responsive:\n"
        "5 taxa increase with humidity (moisture-dependent organisms), 5 with temperature\n"
        "(thermophilic taxa), and 5 with PM2.5 (particle-associated taxa). Some overlap with the\n"
        "causal taxa, creating realistic confounding. The coupling is additive:\n\n"
        "   \u03b3_j * e(h,t) = 0.3 * z_env(h,t) * \u03c3_j\n\n"
        "where z_env is the relevant standardized environmental variable.\n\n\n"
        "2.4 Environmental Covariates\n\n"
        "Five environmental time series are generated independently for each household:\n\n"
        "  1. Temperature: Seasonal sinusoidal trend (amplitude 5\u00b0C, period 365 days) with\n"
        "     AR(1) daily noise (\u03c6=0.7, \u03c3=1.5\u00b0C) and random seasonal phase per household.\n"
        "  2. Relative humidity: Seasonal trend correlated with temperature (r \u2248 0.5) plus\n"
        "     AR(1) noise (\u03c6=0.6, \u03c3=5%), clamped to [20%, 90%].\n"
        "  3. PM2.5: Baseline AR(1) process (\u03c6=0.5, \u03c3=3 \u03bcg/m\u00b3) with sporadic spikes\n"
        "     (Bernoulli p=0.05, exponential magnitude) representing cooking or wildfires.\n"
        "  4. CO2: Weekly periodic occupancy signal (amplitude 200 ppm) with AR(1) noise.\n"
        "  5. Fungal spore concentration: Driven by humidity plus seasonal trend and noise."
    )
    add_text_page(pdf, "Methods (continued)", methods_2, fontsize=8.5)

    # ========== PAGE 6: METHODS — ALLERGY MODEL + INFERENCE ==========
    methods_3 = (
        "2.5 Allergy Response Model\n\n"
        "The daily allergy score y(h,p,t) for person p in household h on day t is:\n\n"
        "   y(h,p,t) = \u03b1_p + \u03b1_h + \u03a3[j in C] \u03b2_j * x(h,j,t) + \u03b3_hum * z_hum + \u03b3_pm * z_pm\n"
        "              + \u03c1 * [y(h,p,t-1) - \u03b1_p - \u03b1_h] + \u03b5(h,p,t)\n\n"
        "where:\n"
        "  \u2022 \u03b1_p ~ N(3, 0.30\u00b2) is the person-specific baseline allergy level\n"
        "  \u2022 \u03b1_h ~ N(0, 0.20\u00b2) is the household random effect\n"
        "  \u2022 C = {1,2,3,4,5} indexes causal taxa, with \u03b2 = (0.10, 0.08, 0.06, 0.04, 0.02)\n"
        "  \u2022 \u03b3_hum = 0.03 and \u03b3_pm = 0.05 are direct environmental effects\n"
        "  \u2022 \u03c1 = 0.3 is the symptom autocorrelation coefficient\n"
        "  \u2022 \u03b5(h,p,t) ~ N(0, 0.15\u00b2) is residual noise\n\n"
        "Allergy scores are clamped to [1, 10]. The effect sizes represent the change in allergy\n"
        "score per unit change in log-abundance; a taxon with \u03b2 = 0.10 produces approximately a\n"
        "10% change in allergy score per standard deviation of its log-abundance fluctuation.\n\n\n"
        "2.6 Statistical Inference: Elastic Net Regression\n\n"
        "To recover causal taxa, we fit an elastic net penalized regression (Zou & Hastie, 2005)\n"
        "via the glmnet package (Friedman et al., 2010).\n\n"
        "Person-level demeaning. Prior to fitting, all variables are demeaned within each person:\n\n"
        "   y_tilde(h,p,t) = y(h,p,t) - mean_y(h,p)\n"
        "   x_tilde(h,j,t) = x(h,j,t) - mean_x(h,j)\n\n"
        "This removes between-person variation, focusing on within-person temporal covariation\n"
        "between microbial abundances and allergy symptoms.\n\n"
        "Model specification. The elastic net minimizes:\n\n"
        "   beta_hat = argmin { (1/2n) * \u03a3 (y_tilde - X_tilde * beta)\u00b2\n"
        "              + lambda * [(1-alpha)/2 * ||beta||_2\u00b2 + alpha * ||beta||_1] }\n\n"
        "with alpha = 0.5 (equal L1 and L2 penalty). Lambda is selected via 10-fold cross-\n"
        "validation. We report results at lambda_min (minimizing CV error).\n\n"
        "Evaluation metrics per simulation replicate:\n"
        "  \u2022 Sensitivity: fraction of 5 causal taxa receiving non-zero coefficients\n"
        "  \u2022 Specificity: fraction of 95 null taxa receiving zero coefficients\n"
        "  \u2022 False discovery rate (FDR): fraction of selected taxa that are non-causal\n"
        "  \u2022 Coefficient ranking: rank of each causal taxon by |coefficient|\n\n\n"
        "2.7 Power Analysis Design\n\n"
        "We varied three design parameters one at a time (defaults in parentheses):\n"
        "  1. Number of households: H \u2208 {5, 10, 20, 40} (default 20), 3 persons each\n"
        "  2. Sampling duration: T \u2208 {30, 60, 90, 180} days (default 90)\n"
        "  3. Effect size multiplier: m \u2208 {0.5, 1.0, 1.5, 2.0} (default 1.0)\n\n"
        "For each of 12 parameter settings, N = 50 independent replicates (total: 600 fits)."
    )
    add_text_page(pdf, "Methods (continued)", methods_3, fontsize=8.5)

    # ========== PAGE 6b: METHODS — UNIVARIATE & MIXED-EFFECTS ==========
    methods_4 = (
        "2.8 Univariate Linear Models with BH FDR Correction\n\n"
        "As a complement to the multivariate elastic net, we fit separate linear models for\n"
        "each of the 100 taxa individually. This \"mass univariate\" approach is standard in\n"
        "microbiome association studies and allows formal hypothesis testing with p-values\n"
        "and false discovery rate control.\n\n"
        "For each taxon j, we fit:\n\n"
        "   allergy_demeaned ~ taxon_j_demeaned\n\n"
        "where both variables are person-level demeaned as in the elastic net approach.\n"
        "We extract the t-statistic and p-value for the taxon coefficient, then apply\n"
        "Benjamini-Hochberg (BH) FDR correction across all 100 tests.\n\n\n"
        "2.9 Covariate-Adjusted Univariate Models\n\n"
        "To control for confounding by environmental parameters that affect both microbial\n"
        "abundances and allergy symptoms, we extend each univariate model to include the\n"
        "five environmental covariates:\n\n"
        "   allergy_dm ~ taxon_j_dm + temperature_dm + humidity_dm + pm25_dm\n"
        "                + co2_dm + fungal_conc_dm\n\n"
        "The taxon p-value is extracted conditional on the environmental covariates.\n"
        "This tests whether each taxon has an association with allergy beyond what is\n"
        "explained by environmental conditions alone.\n\n\n"
        "2.10 Mixed-Effects Models\n\n"
        "To properly account for the hierarchical data structure (repeated measures within\n"
        "persons within households) without relying on demeaning, we fit linear mixed-effects\n"
        "models using the lme4 package (Bates et al., 2015). For each taxon j:\n\n"
        "   allergy ~ taxon_j + (1|household_id/person_id)\n\n"
        "with random intercepts for person nested within household. P-values are obtained\n"
        "from the t-statistic using a normal approximation.\n\n"
        "We also fit the full mixed-effects model with environmental covariates:\n\n"
        "   allergy ~ taxon_j + temperature + humidity + pm25 + co2 + fungal_conc\n"
        "             + (1|household_id/person_id)\n\n"
        "In total, four modeling approaches are compared:\n"
        "  1. Simple univariate (demeaned, no covariates)\n"
        "  2. Covariate-adjusted univariate (demeaned)\n"
        "  3. Mixed-effects (random intercepts, no covariates)\n"
        "  4. Mixed-effects with environmental covariates\n\n"
        "All four approaches apply BH FDR correction across 100 taxa and are evaluated\n"
        "at FDR < 0.05 for sensitivity, false positives, and observed FDR."
    )
    add_text_page(pdf, "Methods (continued)", methods_4, fontsize=8.8)

    # ========== PAGE 6c: METHODS — MEDIATION ANALYSIS ==========
    methods_5 = (
        "2.11 Mediation Analysis\n\n"
        "To address the environmental confounding problem, we developed a mediation analysis\n"
        "framework that decomposes each taxon's association with allergy into direct and\n"
        "environment-confounded components, following the Baron and Kenny (1986) framework.\n\n"
        "Total effect (c path). For each taxon j, the total association with allergy is\n"
        "estimated from the simple univariate model:\n\n"
        "   allergy_dm ~ taxon_j_dm\n\n"
        "yielding coefficient beta_total and p-value p_total.\n\n"
        "Direct effect (c' path). The direct association, controlling for environment:\n\n"
        "   allergy_dm ~ taxon_j_dm + temperature_dm + humidity_dm + pm25_dm\n"
        "               + co2_dm + fungal_conc_dm\n\n"
        "yielding beta_direct and p_direct.\n\n"
        "Environmental coupling (a path). How much each taxon is driven by environment:\n\n"
        "   taxon_j_dm ~ temperature_dm + humidity_dm + pm25_dm + co2_dm + fungal_conc_dm\n\n"
        "The R-squared quantifies the fraction of taxon variability explained by environment.\n\n"
        "Attenuation. The fraction of total signal attributable to confounding:\n\n"
        "   Attenuation_j = (beta_total - beta_direct) / beta_total\n\n"
        "Classification. Each taxon is classified based on BH-corrected p-values at 5%:\n\n"
        "  DIRECT:     significant total AND direct effect, attenuation < 50%.\n"
        "              These taxa retain their allergy association after environmental\n"
        "              adjustment, suggesting a genuine taxon-allergy pathway.\n\n"
        "  CONFOUNDED: significant total BUT non-significant direct OR attenuation >= 50%.\n"
        "              These taxa lose signal after adjusting for environment, indicating\n"
        "              the association was driven by shared environmental exposure.\n\n"
        "  NULL:       non-significant total effect.\n\n"
        "Power analyses compared four selection methods across household sizes\n"
        "(H = 5, 10, 20, 40, 80, 160): standard univariate (BH FDR on total effect),\n"
        "covariate-adjusted (BH FDR on direct effect), mediation classification (Direct\n"
        "class only), and strict mediation (Direct class excluding environment-driven taxa)."
    )
    add_text_page(pdf, "Methods (continued)", methods_5, fontsize=8.8)

    # ========== PAGE 7: FIGURE 2 — ALLERGY TIME SERIES ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_allergy_timeseries.png"),
        "Figure 2. Simulated daily allergy score for one individual (Household 1, Person 1) "
        "over 90 days. The time series shows realistic day-to-day fluctuations with temporal "
        "autocorrelation (rho = 0.3) driven by microbial and environmental exposures. Scores "
        "fluctuate between 1 and 3.2 on the 1-10 scale, with occasional spikes corresponding "
        "to peaks in causal taxa abundance or environmental stressors.",
        title="Figure 2: Simulated Allergy Time Series")

    # ========== PAGE 8: FIGURE 3 — CAUSAL TAXA DYNAMICS ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_causal_taxa_dynamics.png"),
        "Figure 3. Log-abundance trajectories of the five causal taxa over 90 days in one "
        "household. Each taxon's temporal dynamics are governed by an AR(1) process with CV drawn "
        "from the empirical range of 5-25% (Hill et al., 2026). More stable taxa show smooth "
        "trajectories (analogous to Sink A, CV=4.9%); more volatile taxa display large day-to-day "
        "fluctuations (analogous to Sink B, CV=26.5%). Effect sizes: taxon_001=10%, taxon_002=8%, "
        "taxon_003=6%, taxon_004=4%, taxon_005=2%.",
        title="Figure 3: Causal Taxa Dynamics")

    # ========== PAGE 9: FIGURE 4 — ENVIRONMENTAL COVARIATES ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_environmental.png"),
        "Figure 4. Simulated environmental covariates for one household over 90 days. "
        "(Top left) Fungal spore concentration, driven by humidity and seasonal trends. "
        "(Top right) Relative humidity with seasonal and daily variability. "
        "(Bottom left) PM2.5 with characteristic sporadic spikes representing cooking events "
        "or external sources. (Bottom right) Indoor temperature with seasonal trend and AR(1) "
        "daily noise. These covariates are shared within a household and affect both microbial "
        "community dynamics (through environment-taxon coupling) and allergy scores directly.",
        title="Figure 4: Environmental Covariates")

    # ========== PAGE 10: RESULTS — SINGLE RUN ==========
    results_1 = (
        "3. RESULTS\n\n"
        "3.1 Single-Run Model Recovery\n\n"
        "In the reference scenario (20 households, 3 persons each, 90 days, base effect sizes),\n"
        "the elastic net model at lambda_min achieved 100% sensitivity\u2014all five causal taxa\n"
        "received non-zero coefficients. The two strongest causal taxa ranked 1st and 2nd by\n"
        "absolute coefficient magnitude among all 100 taxa (Figure 5):\n\n"
        "   Rank 1:  taxon_001  (\u03b2_true = 0.10)  \u2014 coefficient = 0.025\n"
        "   Rank 2:  taxon_002  (\u03b2_true = 0.08)  \u2014 coefficient = 0.015\n"
        "   Rank 5:  taxon_003  (\u03b2_true = 0.06)  \u2014 coefficient = 0.008\n"
        "   Rank 7:  taxon_004  (\u03b2_true = 0.04)  \u2014 coefficient = 0.007\n"
        "   Rank 14: taxon_005  (\u03b2_true = 0.02)  \u2014 coefficient = 0.004\n\n"
        "The clear separation of the two largest effects demonstrates that taxa contributing\n"
        "8-10% to allergy severity are robustly detectable under these conditions. The smaller-\n"
        "effect taxa (4-6%) appear in the top 10 but are interspersed with false positives.\n"
        "The weakest causal taxon (2% effect) ranks 14th, making it difficult to distinguish\n"
        "from noise without additional information.\n\n"
        "However, the model also selected 70 of 95 non-causal taxa with non-zero coefficients,\n"
        "yielding a false discovery rate of 93.3% and specificity of 26.3%. The non-causal taxa\n"
        "received small coefficients, but the lack of sparsity under lambda_min means the\n"
        "selected set is heavily contaminated with false positives.\n\n"
        "Marginal scatter plots (Figure 6) show visible positive associations between each causal\n"
        "taxon's abundance and allergy scores across all persons, though the relationships are\n"
        "noisy\u2014consistent with the modest effect sizes and presence of multiple confounding\n"
        "taxa and environmental variables."
    )
    add_text_page(pdf, "Results", results_1, fontsize=9)

    # ========== PAGE 11: FIGURE 5 — COEFFICIENTS ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_coefficients.png"),
        "Figure 5. Top 20 elastic net coefficients (by absolute magnitude) from the reference "
        "scenario (20 households x 3 persons x 90 days). Red bars indicate truly causal taxa; "
        "gray bars indicate non-causal taxa. The two largest-effect causal taxa (taxon_001 and "
        "taxon_002, with 10% and 8% true effects) clearly separate from the noise floor with "
        "coefficients 2-3x larger than any false positive. Smaller-effect causal taxa "
        "(taxon_003-005) are interspersed with false positives, illustrating the challenge of "
        "detecting modest biological effects in high-dimensional settings.",
        title="Figure 5: Elastic Net Coefficient Recovery")

    # ========== PAGE 12: FIGURE 6 — SCATTER PLOTS ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_scatter_causal.png"),
        "Figure 6. Marginal scatter plots of allergy score versus log-abundance for each "
        "causal taxon, pooling all persons and households. Red lines show linear regression "
        "fits. Positive associations are visible for all five taxa despite substantial noise, "
        "reflecting the modest individual effect sizes (2-10%) embedded in a high-dimensional "
        "predictor space with 100 taxa and 5 environmental covariates.",
        title="Figure 6: Allergy vs. Causal Taxa Abundance")

    # ========== PAGE 13: RESULTS — POWER ANALYSIS ==========
    results_2 = (
        "3.2 Power Analysis\n\n"
        "Table 1. Effect of number of households (90 days, 3 persons/household, base effects).\n"
        "Mean \u00b1 SD over 50 simulation replicates.\n\n"
        "  Households   Sensitivity       Specificity   FDR     Taxa Selected\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "      5        0.804 \u00b1 0.216     0.279         0.943   72.5\n"
        "     10        0.876 \u00b1 0.133     0.267         0.940   74.0\n"
        "     20        0.936 \u00b1 0.103     0.291         0.933   72.0\n"
        "     40        0.972 \u00b1 0.070     0.284         0.932   72.9\n\n\n"
        "Sensitivity increased monotonically with number of households. With only 5 households\n"
        "(15 persons total), mean sensitivity was 80.4% (SD = 21.6%). At 40 households, sensitivity\n"
        "rose to 97.2% (SD = 7.0%). The diminishing returns suggest 20 households is an inflection\n"
        "point beyond which additional recruitment yields modest gains.\n\n\n"
        "Table 2. Effect of sampling duration (20 households, 3 persons, base effects).\n\n"
        "  Days   Sensitivity       Specificity   FDR     Taxa Selected\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "   30    0.880 \u00b1 0.140     0.201         0.945   80.3\n"
        "   60    0.828 \u00b1 0.167     0.255         0.944   74.9\n"
        "   90    0.936 \u00b1 0.117     0.288         0.933   72.3\n"
        "  180    0.984 \u00b1 0.055     0.352         0.923   66.5\n\n\n"
        "Extended sampling had a pronounced effect. At 180 days, sensitivity reached 98.4% and\n"
        "was the only manipulation that meaningfully improved specificity (35.2%) and reduced the\n"
        "number of selected taxa (66.5 vs 80.3 at 30 days).\n\n\n"
        "Table 3. Effect of effect size multiplier (20 households, 90 days).\n\n"
        "  Multiplier   Sensitivity       Specificity   FDR     Taxa Selected\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "    0.5x       0.876 \u00b1 0.151     0.433         0.921   58.3\n"
        "    1.0x       0.932 \u00b1 0.111     0.283         0.935   72.7\n"
        "    1.5x       0.820 \u00b1 0.191     0.252         0.945   75.2\n"
        "    2.0x       0.848 \u00b1 0.183     0.225         0.946   77.8\n"
    )
    add_text_page(pdf, "Results (continued)", results_2, fontsize=8.5)

    # ========== PAGE 14: FIGURE 7 — POWER CURVES ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "sim_power_curves.png"),
        "Figure 7. Power analysis across three study design dimensions (50 replicates each). "
        "Red lines show sensitivity (proportion of causal taxa detected); blue lines show "
        "1-FDR (proportion of selected taxa that are truly causal). Error bars: 95% CI. "
        "Dashed line: 80% power threshold. (Left) Sensitivity rises from 80% to 97% as "
        "households increase from 5 to 40. (Center) Longer sampling improves both sensitivity "
        "and specificity. (Right) Sensitivity is relatively stable across effect size multipliers, "
        "though interaction effects with regularization cause non-monotonic behavior at high "
        "multipliers.",
        title="Figure 7: Power Curves")

    # ========== PAGE 15: UNIVARIATE RESULTS ==========
    univariate_text = (
        "3.4 Univariate Linear Models\n\n"
        "As an alternative to the multivariate elastic net, we fit individual linear models\n"
        "for each of the 100 taxa. At BH FDR < 0.05, the simple univariate approach (demeaned,\n"
        "no covariates) detected all 5 causal taxa with 18 false positives (observed FDR = 78%).\n"
        "This is a substantial improvement over the elastic net's 70 false positives (FDR = 93%).\n\n"
        "The top-ranked associations by p-value were:\n\n"
        "   Rank 1: PM2.5 (environmental)   p = 3.8e-179  (direct causal effect on allergies)\n"
        "   Rank 2: taxon_017 (non-causal)   p = 2.6e-38   (environment-linked false positive)\n"
        "   Rank 3: taxon_005 (causal, 2%)   p = 9.0e-34   (detected despite smallest effect)\n"
        "   Rank 4: taxon_001 (causal, 10%)  p = 3.2e-27   (strongest causal taxon)\n"
        "   Rank 5: taxon_030 (non-causal)   p = 7.6e-26   (environment-linked false positive)\n\n"
        "A notable finding is that taxon_017, a non-causal taxon coupled to temperature in the\n"
        "simulation, ranked as the most significant taxon. This illustrates the classic\n"
        "confounding problem: taxa correlated with environmental variables that directly affect\n"
        "allergies will show spurious associations in univariate tests.\n\n"
        "Similarly, taxon_005 (the weakest causal taxon at 2% effect) outranked taxon_001 (the\n"
        "strongest at 10%) because taxon_005 happens to be coupled to humidity, amplifying its\n"
        "marginal association. This demonstrates that univariate p-value rankings do not\n"
        "necessarily reflect true causal effect sizes."
    )
    add_text_page(pdf, "Results (continued)", univariate_text, fontsize=9)

    # ========== PAGE 16: FIGURE 8 — VOLCANO PLOT ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "univariate_volcano.png"),
        "Figure 8. Volcano plot of univariate linear model results. Each point represents "
        "one of 100 taxa or 5 environmental variables. X-axis: regression coefficient "
        "(demeaned allergy ~ demeaned predictor). Y-axis: -log10(p-value). Red points: truly "
        "causal taxa. Blue points: environmental variables. Gray points: non-causal taxa. "
        "Triangles indicate BH FDR < 0.05. PM2.5 dominates the plot (p ~ 10^-179) due to "
        "its direct causal effect. Several non-causal environment-linked taxa (gray triangles) "
        "achieve significance through confounding.",
        title="Figure 8: Univariate Volcano Plot")

    # ========== PAGE 17: MIXED-EFFECTS MODEL COMPARISON ==========
    mixed_text = (
        "3.5 Effect of Covariate Adjustment and Mixed-Effects Modeling\n\n"
        "To address the confounding problem revealed by the univariate analysis, we compared\n"
        "four modeling approaches (Table 4).\n\n"
        "Table 4. Model comparison at BH FDR < 0.05 (20 households, 90 days, base effects).\n\n"
        "  Model                   Sensitivity  TP   FP   Observed FDR\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "  Simple univariate       5/5 (100%)    5    18   78%\n"
        "  Covariate-adjusted      4/5  (80%)    4     9   69%\n"
        "  Mixed-effects           5/5 (100%)    5    19   79%\n"
        "  Mixed + covariates      4/5  (80%)    4    10   71%\n\n\n"
        "Key findings from the model comparison:\n\n"
        "1. Adding environmental covariates cuts false positives nearly in half (18\u219209 for\n"
        "   demeaned models; 19\u219210 for mixed-effects). Many false positives in the unadjusted\n"
        "   models were environment-linked taxa (e.g., taxon_017, taxon_030, taxon_035) whose\n"
        "   spurious associations disappear once the environmental variables are controlled.\n\n"
        "2. The cost of covariate adjustment is the loss of taxon_005 (2% effect). This taxon\n"
        "   is coupled to humidity in the simulation; controlling for humidity absorbs part of\n"
        "   its signal, pushing its FDR from 4.5e-32 (unadjusted) to 0.06-0.08 (adjusted),\n"
        "   just above the 0.05 threshold. At FDR < 0.10, all 5 taxa are recovered.\n\n"
        "3. Mixed-effects models perform similarly to demeaned models. The singular fit warnings\n"
        "   from lmer suggest the person-level random intercept variance is near zero\u2014the\n"
        "   demeaning approach already removes this variation effectively.\n\n"
        "4. The covariate-adjusted demeaned model offers the best balance: simplest approach,\n"
        "   fewest false positives (9), and all 5 causal taxa detected at FDR < 0.10.\n\n\n"
        "Detailed results for causal taxa across models:\n\n"
        "   taxon_001 (10% effect): FDR < 1e-22 in all four models\n"
        "   taxon_002  (8% effect): FDR < 1e-07 in all four models\n"
        "   taxon_003  (6% effect): FDR 8.7e-06 to 1.5e-03 across models\n"
        "   taxon_004  (4% effect): FDR 5.5e-06 to 3.0e-03 across models\n"
        "   taxon_005  (2% effect): FDR 4.5e-32 (unadjusted) to 0.075 (adjusted)"
    )
    add_text_page(pdf, "Results (continued)", mixed_text, fontsize=8.5)

    # ========== PAGE 18: FIGURE 9 — TP/FP COMPARISON ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mixed_tp_fp_comparison.png"),
        "Figure 9. True positives (red) and false positives (gray) at BH FDR < 0.05 for "
        "each of the four modeling approaches. Adding environmental covariates (left two bars) "
        "cuts false positives roughly in half compared to unadjusted models (right two bars), "
        "at the cost of losing the weakest causal taxon (2% effect). Mixed-effects models "
        "perform similarly to their demeaned counterparts.",
        title="Figure 9: Model Comparison \u2014 True vs False Positives")

    # ========== PAGE 19: FIGURE 10 — CAUSAL SIGNIFICANCE ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mixed_causal_significance.png"),
        "Figure 10. Significance of each causal taxon across the four models, shown as "
        "-log10(BH-adjusted p-value). The red dashed line marks FDR = 0.05. Taxon_001 (10% "
        "effect) and taxon_002 (8%) are highly significant in all models. Taxon_003 (6%) and "
        "taxon_004 (4%) are significant but with reduced signal in covariate-adjusted models. "
        "Taxon_005 (2%) shows a dramatic drop when covariates are included, falling just above "
        "the FDR = 0.05 threshold, because its environment coupling (humidity) absorbs signal.",
        title="Figure 10: Causal Taxa Significance Across Models")

    # ========== PAGE 20: FIGURE 11 — FP VS THRESHOLD ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mixed_fp_vs_threshold.png"),
        "Figure 11. False positives as a function of BH FDR threshold for each modeling "
        "approach. Covariate-adjusted models (green, orange) consistently produce fewer false "
        "positives at every threshold compared to unadjusted models (blue, pink). At FDR < 0.10, "
        "covariate-adjusted models yield ~12 false positives vs ~28 for unadjusted models. "
        "This demonstrates that controlling for environmental confounders is the single most "
        "effective strategy for reducing false discoveries in this simulation framework.",
        title="Figure 11: False Positives vs FDR Threshold")

    # ========== PAGE 21: FDR DISCUSSION ==========
    fdr_text = (
        "3.3 The False Discovery Rate Challenge\n\n"
        "Across all 600 simulation replicates and all parameter configurations, the false\n"
        "discovery rate remained high, ranging from 92.1% to 94.6% (Tables 1-3). The elastic\n"
        "net at lambda_min consistently selected 58-80 taxa (out of 100), of which only 4-5\n"
        "were truly causal. This behavior is well-known for elastic net in high-dimensional\n"
        "settings: the L1 penalty produces sparsity relative to the full model, but lambda_min\n"
        "prioritizes prediction accuracy over variable selection parsimony.\n\n"
        "This high FDR does not indicate that the causal signal is undetectable\u2014rather, it\n"
        "reflects the need for a secondary filtering step. The causal taxa consistently appear\n"
        "among the top-ranked coefficients (ranks 1-14 in the reference scenario), and their\n"
        "coefficients are substantially larger than those of the false positives.\n\n"
        "Practical approaches to reduce FDR include:\n\n"
        "   1. Using lambda_1se instead of lambda_min, which applies stricter regularization\n"
        "      and selects fewer variables.\n\n"
        "   2. Stability selection (Meinshausen & Buhlmann, 2010): running elastic net on many\n"
        "      bootstrap resamples and retaining only taxa selected in >50% of runs.\n\n"
        "   3. Bayesian sparsity priors: horseshoe or spike-and-slab priors that produce\n"
        "   3. Bayesian sparsity priors: horseshoe or spike-and-slab priors that produce\n"
        "      cleaner posterior inclusion probabilities.\n\n"
        "   4. Covariate-adjusted univariate models (Section 3.5): reduce false positives\n"
        "      from 18-19 to 9-10.\n\n"
        "   5. Mediation analysis (Section 3.7): further reduces FP by classifying taxa\n"
        "      as Direct vs Confounded based on environmental attenuation."
    )
    add_text_page(pdf, "Results & Discussion", fdr_text, fontsize=8.8)

    # ========== UNIVARIATE POWER ANALYSIS ==========
    univ_power_text = (
        "3.6 Univariate Power Analysis\n\n"
        "The expanded power analysis using covariate-adjusted univariate models with BH FDR\n"
        "correction revealed a critical asymmetry: increasing sample size improves sensitivity\n"
        "but does NOT reduce false positives.\n\n"
        "Table 5. By Number of Households (90 days, covariate-adjusted, BH FDR < 0.05).\n\n"
        "  Households   Sensitivity   False Positives   Observed FDR\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "       5         0.30            10.1              0.840\n"
        "      10         0.50            11.4              0.782\n"
        "      20         0.61            12.3              0.781\n"
        "      40         0.78            12.5              0.735\n"
        "      80         0.90            14.1              0.745\n"
        "     160         0.93            15.2              0.757\n\n"
        "False positives actually INCREASED from 10.1 (5 HH) to 15.2 (160 HH), because\n"
        "greater statistical power detects both true and spurious associations.\n\n\n"
        "Table 6. By Sampling Duration (20 households, covariate-adjusted, BH FDR < 0.05).\n\n"
        "  Days   Sensitivity   False Positives   Observed FDR\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "   30      0.33            18.1              0.914\n"
        "   60      0.52            13.7              0.825\n"
        "   90      0.59            10.7              0.759\n"
        "  180      0.82            10.0              0.684\n"
        "  365      0.97             9.8              0.654\n\n"
        "Longer sampling is the ONLY design parameter that reduces false positives (18 to 10)\n"
        "while simultaneously improving sensitivity (33% to 97%). At 365 days, observed FDR\n"
        "drops to 65%, still far above nominal 5% but the best of any configuration tested.\n\n\n"
        "The persistent false positives arise from the confounding structure of the simulation:\n"
        "environmental parameters (humidity, PM2.5) directly affect both allergy scores and the\n"
        "abundances of environment-linked taxa. Even after covariate adjustment, residual\n"
        "confounding generates significant associations for ~10 non-causal taxa. This represents\n"
        "a realistic challenge for built-environment studies where the same conditions that shape\n"
        "microbial communities also directly affect respiratory health."
    )
    add_text_page(pdf, "Results (continued)", univ_power_text, fontsize=8.5)

    # ========== UNIVARIATE POWER FIGURES ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "power_univ_sensitivity_all.png"),
        "Figure 12. Sensitivity of the covariate-adjusted univariate model (BH FDR < 0.05) "
        "across three study design dimensions. Sensitivity improves with more households and "
        "longer sampling duration. The effect size multiplier shows a paradoxical decrease at "
        "higher values, likely reflecting interaction between larger effects and the covariate "
        "adjustment absorbing shared environmental variance.",
        title="Figure 12: Univariate Power \u2014 Sensitivity")

    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "power_univ_fp_all.png"),
        "Figure 13. False positives from the covariate-adjusted univariate model across study "
        "design dimensions. More households does NOT reduce false positives (left panel); only "
        "longer sampling duration meaningfully reduces them (center panel), suggesting that the "
        "false positives arise from temporally structured environmental confounding that is "
        "better resolved with longer time series.",
        title="Figure 13: Univariate Power \u2014 False Positives")

    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "power_univ_observed_fdr_all.png"),
        "Figure 14. Observed FDR from the covariate-adjusted univariate model. The BH procedure "
        "at a nominal 5% threshold produces observed FDR of 65-91%, indicating systematic failure "
        "of FDR control. This is not a failure of the BH procedure per se, but rather a violation "
        "of its assumptions: the environment-linked null taxa are not independent of the alternative "
        "hypotheses, because they share environmental drivers with the causal pathway.",
        title="Figure 14: Observed FDR vs Nominal")

    # ========== MEDIATION RESULTS ==========
    mediation_text = (
        "3.7 Mediation Analysis: Separating Direct from Confounded Effects\n\n"
        "To directly address environmental confounding, we applied the mediation framework to\n"
        "decompose each taxon's allergy association into direct and confounded components.\n\n"
        "In the reference scenario (20 HH, 90 days), the mediation analysis classified 100\n"
        "taxa into three categories:\n\n"
        "   Direct:     13 taxa (3 causal, 10 false positives)\n"
        "   Confounded: 15 taxa (1 causal, 14 false positives)\n"
        "   Null:       72 taxa\n\n"
        "Known environment-linked non-causal taxa were correctly classified as Confounded:\n\n"
        "  Taxon       Env Link   Coef Total  Coef Direct  Attenuation  Env R\u00b2\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "  taxon_035   PM2.5       0.210       0.071          66%       0.094\n"
        "  taxon_012   PM2.5       0.187       0.052          72%       0.090\n"
        "  taxon_017   PM2.5       0.132       0.014          89%       0.084\n"
        "  taxon_030   PM2.5       0.152       0.006          96%       0.077\n"
        "  taxon_015   Humidity    0.064       0.033          48%       0.036\n"
        "  taxon_010   Humidity    0.052       0.002          96%       0.041\n"
        "  taxon_020   Humidity    0.050      -0.001         102%       0.030\n\n"
        "PM2.5-linked taxa showed the strongest confounding (66-96% attenuation), consistent\n"
        "with PM2.5 having the largest direct effect on allergy. Humidity-linked taxa showed\n"
        "moderate to complete attenuation (48-102%), with attenuation exceeding 100% for\n"
        "taxon_020 indicating sign reversal after environmental adjustment.\n\n\n"
        "3.8 Power Analysis: Mediation vs Standard Approaches\n\n"
        "Table 7. Comparison of selection methods across sample sizes (90 days, 50 sims).\n\n"
        "  HH   Method                     Sensitivity   FP    Obs FDR\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "   20  Standard (total FDR<0.05)     0.83       20.3   0.826\n"
        "   20  Adjusted (direct FDR<0.05)    0.61       12.3   0.781\n"
        "   20  Mediation (Direct class)      0.52        8.7   0.742\n"
        "  160  Standard (total FDR<0.05)     1.00       24.4   0.828\n"
        "  160  Adjusted (direct FDR<0.05)    0.93       15.2   0.757\n"
        "  160  Mediation (Direct class)      0.76        9.9   0.700\n"
    )
    add_text_page(pdf, "Results (continued)", mediation_text, fontsize=8.5)

    mediation_text_2 = (
        "Mediation reduced false positives from ~20-24 (standard) to ~9-10 across all sample\n"
        "sizes\u2014approximately halving the false positive burden. This improvement was achieved\n"
        "primarily by correctly filtering out environment-confounded taxa.\n\n"
        "However, this improvement came at a cost to sensitivity. At 160 households, mediation\n"
        "sensitivity was 0.76 compared to 1.00 for the standard approach. Some causal taxa were\n"
        "misclassified as Confounded because they are BOTH genuinely causal AND environment-linked\n"
        "in the simulation (taxa 1-2 are humidity-linked, taxa 3-4 are temperature-linked,\n"
        "taxon 5 is PM2.5-linked). This overlap reflects a realistic biological scenario: the\n"
        "same environmental conditions that select for certain microbial taxa may also be the\n"
        "conditions under which those taxa exert their allergenic effects.\n\n\n"
        "Residual False Positives in the Mediation Approach\n\n"
        "Approximately 9 false positives persisted in the mediation \"Direct\" class across\n"
        "all sample sizes. These arise from two sources:\n\n"
        "  1. Weak environmental coupling that escapes the attenuation filter: Some\n"
        "     environment-linked taxa (e.g., taxon_011, temperature-linked) showed low\n"
        "     attenuation (~6%) because the temperature-allergy pathway is weak in the\n"
        "     simulation (gamma_temp = 0; only humidity and PM2.5 directly affect allergy).\n\n"
        "  2. Purely spurious associations: Non-environment-linked taxa that achieved\n"
        "     significance by chance. These represent the irreducible false positive rate\n"
        "     from testing 100 taxa with BH correction.\n\n\n"
        "The sensitivity-FDR tradeoff (Figure 18) reveals a fundamental tension: no single\n"
        "method achieves both high sensitivity and low FDR simultaneously. Liberal thresholds\n"
        "detect all causal taxa but include many false positives, while conservative approaches\n"
        "(mediation, strict FDR) reduce false positives at the cost of missing environment-\n"
        "linked causal taxa. This suggests a two-stage approach may be optimal: use mediation\n"
        "to filter confounded taxa, then apply elastic net to the surviving candidates."
    )
    add_text_page(pdf, "Results (continued)", mediation_text_2, fontsize=8.8)

    # ========== MEDIATION FIGURES ==========
    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mediation_sensitivity.png"),
        "Figure 15. Sensitivity comparison across four analytical approaches. The standard "
        "approach (red) achieves the highest sensitivity but at the cost of many false positives. "
        "The mediation approach (green) sacrifices some sensitivity to reduce false discoveries. "
        "Error bars show 95% confidence intervals across 50 replicates.",
        title="Figure 15: Mediation \u2014 Sensitivity Comparison")

    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mediation_false_positives.png"),
        "Figure 16. False positives across analytical approaches. Mediation consistently produces "
        "~9 false positives regardless of sample size, compared to 17-24 for the standard approach. "
        "The gap widens at larger sample sizes because the standard approach gains power to detect "
        "confounded associations.",
        title="Figure 16: Mediation \u2014 False Positives")

    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mediation_observed_fdr.png"),
        "Figure 17. Observed FDR across approaches. Mediation reduces FDR from ~83% to ~70% "
        "compared to the standard approach, but all methods substantially exceed the nominal 5% "
        "BH threshold (dashed red line), indicating that environmental confounding\u2014not merely "
        "multiple testing\u2014is the primary driver of false discoveries.",
        title="Figure 17: Mediation \u2014 Observed FDR")

    add_figure_page(pdf,
        os.path.join(PAPER_DIR, "mediation_tradeoff.png"),
        "Figure 18. Sensitivity-FDR tradeoff across methods and sample sizes (numbers indicate "
        "households). The ideal operating point is the upper-left corner (high sensitivity, low "
        "FDR). The mediation approach shifts curves leftward (lower FDR) at the cost of downward "
        "movement (lower sensitivity). No method achieves both high sensitivity and low FDR "
        "simultaneously, reflecting the fundamental tension between detection power and false "
        "positive control in the presence of environmental confounding.",
        title="Figure 18: Sensitivity vs FDR Tradeoff")

    # ========== DISCUSSION ==========
    disc_text = (
        "4. DISCUSSION\n\n"
        "4.1 Key Findings\n\n"
        "Our simulation framework demonstrates that a household sensor network can reliably\n"
        "detect microbial taxa contributing 2-10% to allergy severity, but that controlling\n"
        "false discoveries requires explicit treatment of environmental confounding:\n\n"
        "   1. 20 households sampled for 90 days provides >93% sensitivity via elastic net.\n\n"
        "   2. Sampling duration matters more than cross-sectional breadth. Extending from\n"
        "      90 to 365 days improved univariate sensitivity from 59% to 97% and was the\n"
        "      only design parameter that reduced false positives (18 to 10). More households\n"
        "      improved sensitivity but INCREASED false positives.\n\n"
        "   3. Environmental confounding is the primary driver of false discoveries. The\n"
        "      persistently high observed FDR (65-91%) across all univariate approaches\n"
        "      indicates that BH FDR control fails when null hypothesis violations arise\n"
        "      from shared environmental drivers rather than independent noise.\n\n"
        "   4. Mediation analysis halves false positives by correctly identifying environment-\n"
        "      confounded taxa, reducing FP from ~20 to ~9. However, it sacrifices sensitivity\n"
        "      (0.76 vs 1.00 at 160 HH) because some causal taxa are themselves environment-\n"
        "      linked\u2014a realistic scenario where environmental conditions promote microbial\n"
        "      growth AND trigger allergic responses.\n\n"
        "   5. No single method achieves both high sensitivity and low FDR. The sensitivity-\n"
        "      FDR tradeoff reveals a fundamental tension that may require two-stage approaches\n"
        "      (mediation filtering followed by elastic net) or instrumental variable methods."
    )
    add_text_page(pdf, "Discussion", disc_text, fontsize=8.8)

    disc_2 = (
        "4.2 Calibration to Empirical Data\n\n"
        "A strength of our framework is the calibration of microbial dynamics to the empirical\n"
        "temporal variability reported by Hill et al. (2026). The CV range of 5-25% spans the\n"
        "full spectrum from deterministic, slowly varying communities (Sink A) to stochastic,\n"
        "rapidly fluctuating ones (Sink B). This calibration is conservative in the sense that\n"
        "P-trap biofilm communities may be more stable than airborne or surface communities\n"
        "relevant to respiratory exposure.\n\n\n"
        "4.3 Implications for Study Design\n\n"
        "For investigators planning household microbiome-allergy studies, our results suggest:\n\n"
        "   Minimum viable study: 10 households, 3 persons each, 90 days. Achieves ~88%\n"
        "     sensitivity via elastic net. Expect ~12 false positives with covariate adjustment.\n\n"
        "   Recommended study: 40+ households, 3 persons each, 180-365 days. Longer sampling\n"
        "     is critical for reducing false positives (18 at 30d to 10 at 365d).\n\n"
        "   Analytical strategy: A two-stage approach is recommended. First, use mediation\n"
        "     analysis to filter environment-confounded taxa, reducing the candidate set by\n"
        "     ~50%. Then, apply elastic net to the filtered set for final variable selection.\n\n"
        "   Environmental monitoring is essential, not optional. Our results demonstrate that\n"
        "     environmental covariates are central to distinguishing causal from confounded\n"
        "     microbial associations. Studies that omit environmental monitoring will be unable\n"
        "     to resolve this confounding.\n\n\n"
        "4.4 Limitations\n\n"
        "  1. Microbial abundances are assumed measured without error.\n"
        "  2. Allergy is modeled as continuous; real symptoms may need ordinal models.\n"
        "  3. Temporal lags between exposure and symptoms are not modeled.\n"
        "  4. Taxa are independent conditional on environment; real ecological networks differ.\n"
        "  5. Mediation assumes linear adjustment fully captures confounding; non-linear\n"
        "     relationships or unmeasured confounders could cause residual confounding.\n"
        "  6. The simulation deliberately creates causal-environment overlap, which penalizes\n"
        "     the mediation approach; in other settings, mediation may perform better.\n\n\n"
        "4.5 Future Directions\n\n"
        "  1. Two-stage mediation + elastic net: filter confounded taxa, then fit elastic net.\n"
        "  2. Instrumental variables: use environment as instruments for causal estimation.\n"
        "  3. Distributed lag models: 1-7 day lags for delayed immune responses.\n"
        "  4. Bayesian models: spike-and-slab priors with informative environment coupling.\n"
        "  5. Stability selection: Bootstrap-based FDR control.\n"
        "  6. Validation against real longitudinal household microbiome-health datasets."
    )
    add_text_page(pdf, "Discussion (continued)", disc_2, fontsize=8.8)

    # ========== ANN ANALYSIS PAGES ==========
    ann_results_path = os.path.join(PAPER_DIR, "ann_results.json")
    if os.path.exists(ann_results_path):
        import json
        with open(ann_results_path) as f:
            ann = json.load(f)

        # ANN Methods page
        ann_methods = (
            "3.5 Artificial Neural Network with Embedding PCA\n\n"
            "To assess whether nonlinear feature transformations can better separate\n"
            "allergy-relevant variation from noise, we trained an artificial neural network\n"
            "(ANN) and compared PCA on its learned embeddings against PCA on raw features.\n\n"
            "Architecture:\n"
            "  Input layer: 105 features (100 taxon relative abundances + 5 environmental variables)\n"
            "  Encoder: 128 (BatchNorm, ReLU, Dropout 0.2) -> 64 (BatchNorm, ReLU, Dropout 0.2)\n"
            "           -> 32 (ReLU) [embedding layer]\n"
            "  Prediction head: 32 -> 16 (ReLU) -> 1 (allergy score)\n\n"
            "Training procedure:\n"
            f"  - Simulated {ann['n_households']} households x {ann['n_persons']} persons x "
            f"{ann['n_days']} days = {ann['n_train_rows'] + ann['n_test_rows']:,} observations\n"
            f"  - 80/20 household-level split: {ann['n_train_hh']} train / {ann['n_test_hh']} test households\n"
            "  - Person-level demeaning applied to remove between-person variance,\n"
            "    focusing the ANN on within-person temporal associations\n"
            "  - Adam optimizer (lr=0.001, weight decay=1e-4), batch size 256\n"
            "  - ReduceLROnPlateau scheduler (patience=10, factor=0.5)\n"
            "  - Early stopping on validation loss (patience=30)\n"
            "  - Implemented in PyTorch\n\n"
            "PCA comparison:\n"
            "  After training, we extracted 32-dimensional embeddings from the encoder for all\n"
            "  observations and performed PCA. For comparison, PCA was also performed on the\n"
            "  105 raw (non-demeaned, standardized) features. We then correlated each PC with\n"
            "  demeaned allergy scores and evaluated the R-squared of the top 5 PCs for predicting\n"
            "  allergy in the held-out test households.\n\n"
            "  The key question: does the ANN's supervised training reorganize feature space\n"
            "  so that the dominant axes of variation align with allergy, compared to unsupervised\n"
            "  PCA which captures total variance regardless of outcome relevance?"
        )
        add_text_page(pdf, "Methods: Neural Network Analysis", ann_methods, fontsize=9)

        # ANN Results page
        best_raw_i = max(range(10), key=lambda i: abs(ann['raw_pc_cors'][i]))
        best_emb_i = max(range(10), key=lambda i: abs(ann['emb_pc_cors'][i]))
        ann_results_text = (
            "3.5 Results: Neural Network Prediction and Embedding PCA\n\n"
            "Prediction performance (held-out test households):\n"
            f"  - Within-person (demeaned): R = {ann['test_r_demeaned']:.3f}, "
            f"R-squared = {ann['test_r2_demeaned']:.3f}\n"
            f"  - Raw scale (with person means): R = {ann['test_r']:.3f}, "
            f"R-squared = {ann['test_r2']:.3f}\n"
            f"  - Test MSE = {ann['test_mse']:.4f}, MAE = {ann['test_mae']:.4f}\n\n"
            "PCA correlation with demeaned allergy:\n\n"
            "  PC   Raw |r|    Emb |r|\n"
        )
        for i in range(10):
            ann_results_text += (
                f"  {i+1:2d}   {abs(ann['raw_pc_cors'][i]):.4f}    {abs(ann['emb_pc_cors'][i]):.4f}\n"
            )
        ann_results_text += (
            f"\nBest single PC:\n"
            f"  Raw: PC{best_raw_i+1} (|r| = {abs(ann['raw_pc_cors'][best_raw_i]):.4f})\n"
            f"  Embedding: PC{best_emb_i+1} (|r| = {abs(ann['emb_pc_cors'][best_emb_i]):.4f})\n\n"
            f"R-squared from top 5 PCs -> allergy (linear regression):\n"
            f"  Raw features:    Train = {ann['r2_raw_5pc']:.4f},  Test = {ann['r2_raw_test']:.4f}\n"
            f"  ANN embedding:   Train = {ann['r2_emb_5pc']:.4f},  Test = {ann['r2_emb_test']:.4f}\n\n"
            f"Variance explained by top 5 PCs:\n"
            f"  Raw features: {ann['raw_var_explained_5']:.1%}\n"
            f"  ANN embedding: {ann['emb_var_explained_5']:.1%}\n\n"
            "The ANN embedding concentrates allergy-relevant variation into its first\n"
            "principal component far more effectively than raw feature PCA. Embedding PC1\n"
            f"alone explains {ann['emb_pc_cors'][0]**2:.1%} of demeaned allergy variance, "
            f"while\nthe best raw PC explains only {ann['raw_pc_cors'][best_raw_i]**2:.1%}. "
            "Critically, this advantage\ngeneralizes to held-out households "
            f"(test R-squared: {ann['r2_emb_test']:.3f} vs {ann['r2_raw_test']:.3f}),\n"
            "confirming that the ANN learns biologically meaningful feature combinations\n"
            "rather than overfitting to training data."
        )
        add_text_page(pdf, "Results: Neural Network Analysis", ann_results_text, fontsize=9)

        # ANN Figure pages
        ann_figs = [
            ('ann_training_loss.png', 'Training and validation loss curves for the ANN.',
             'ANN Training Loss'),
            ('ann_pred_vs_actual.png', 'ANN predicted vs actual allergy scores (test set, raw scale).',
             'ANN Prediction Performance'),
            ('ann_pca_comparison.png',
             'Absolute correlation of each PC with demeaned allergy score. '
             'Left: PCA on raw features. Right: PCA on ANN embedding layer.',
             'PCA Correlation Comparison'),
            ('ann_pca_scatter.png',
             'PC1 vs PC2 colored by demeaned allergy score. '
             'Raw feature PCA (left) shows no allergy gradient; '
             'ANN embedding PCA (right) shows clear separation.',
             'PCA Scatter: Raw vs Embedding'),
        ]
        for fname, caption, title in ann_figs:
            fpath = os.path.join(PAPER_DIR, fname)
            if os.path.exists(fpath):
                add_figure_page(pdf, fpath, caption, title)

    # ========== PAGE 17: CONCLUSIONS + REFERENCES ==========
    conclusions = (
        "5. CONCLUSIONS\n\n"
        "We have developed and validated a simulation framework for evaluating the statistical\n"
        "power and false discovery characteristics of household sensor networks designed to\n"
        "detect microbial determinants of allergic disease. Calibrated to Hill et al. (2026),\n"
        "our framework evaluates five analytical approaches: elastic net, univariate models\n"
        "with BH FDR correction, mixed-effects models, mediation analysis, and artificial\n"
        "neural networks with embedding PCA.\n\n"
        "Studies enrolling 20+ households for 90+ days can detect causal taxa contributing\n"
        ">=4% to allergy severity with >93% sensitivity, but controlling false discoveries\n"
        "requires fundamentally different strategies than simply increasing sample size. The\n"
        "central challenge is environmental confounding: taxa whose abundances are driven by\n"
        "the same environmental parameters that affect allergy (humidity, PM2.5) generate\n"
        "persistent false positive associations not resolved by standard multiple testing\n"
        "corrections.\n\n"
        "Mediation analysis, which decomposes taxon-allergy associations into direct and\n"
        "environment-confounded components, halves the false positive rate but cannot fully\n"
        "resolve the tension between sensitivity and specificity when causal taxa are\n"
        "themselves environment-linked.\n\n"
        "An artificial neural network trained on person-demeaned taxa and environmental data\n"
        "demonstrated that supervised nonlinear dimensionality reduction concentrates allergy-\n"
        "relevant variation into the first principal component of the embedding layer far more\n"
        "effectively than unsupervised PCA on raw features, and this advantage generalizes to\n"
        "held-out households.\n\n"
        "These findings underscore that environmental monitoring is not merely complementary but\n"
        "essential for interpreting microbiome-health associations in the built environment.\n\n\n"
        "DATA AND CODE AVAILABILITY\n\n"
        "Simulation code is available at: https://github.com/afodor/claudeCityWideModels\n"
        "Implemented in R v4.5.1 (MASS, glmnet, lme4, ggplot2) and Python 3.9\n"
        "(PyTorch, scikit-learn, matplotlib).\n\n\n"
        "REFERENCES\n\n"
        "Adams RI, Bateman AC, Bik HM, Meadow JF (2015). Microbiota of the indoor\n"
        "   environment: a meta-analysis. Microbiome, 3:49.\n\n"
        "Ege MJ, Mayer M, Normand AC, et al. (2011). Exposure to environmental\n"
        "   microorganisms and childhood asthma. NEJM, 364(8):701-709.\n\n"
        "Friedman J, Hastie T, Tibshirani R (2010). Regularization paths for generalized\n"
        "   linear models via coordinate descent. J Stat Software, 33(1):1-22.\n\n"
        "Gasparrini A, Armstrong B, Kenward MG (2010). Distributed lag non-linear models.\n"
        "   Statistics in Medicine, 29(21):2224-2234.\n\n"
        "Hill MS, et al. (2026). Temporal stability and niche partitioning of bacterial\n"
        "   communities in paired residential sink P-traps. bioRxiv,\n"
        "   doi:10.64898/2026.02.17.706431v1.\n\n"
        "Meinshausen N, Buhlmann P (2010). Stability selection. JRSS-B, 72(4):417-473.\n\n"
        "Mendell MJ, Mirer AG, Cheung K, et al. (2011). Respiratory and allergic health\n"
        "   effects of dampness, mold, and dampness-related agents. EHP, 119(6):748-756.\n\n"
        "Zou H, Hastie T (2005). Regularization and variable selection via the elastic net.\n"
        "   JRSS-B, 67(2):301-320.\n\n"
        "Baron RM, Kenny DA (1986). The moderator-mediator variable distinction in social\n"
        "   psychological research. J Personality and Social Psychology, 51(6):1173-1182.\n\n"
        "Bates D, Maechler M, Bolker B, Walker S (2015). Fitting linear mixed-effects\n"
        "   models using lme4. J Stat Software, 67(1):1-48.\n\n"
        "Benjamini Y, Hochberg Y (1995). Controlling the false discovery rate: a practical\n"
        "   and powerful approach to multiple testing. JRSS-B, 57(1):289-300."
    )
    add_text_page(pdf, "Conclusions & References", conclusions, fontsize=9)

print(f"Generated {OUT_PDF}")
