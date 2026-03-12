# PreMiEr Microbiome Simulation & Visualization Suite

This repository contains the simulation, statistical analysis, neural network modeling, and interactive 3D visualizations for the PreMiEr (Preventing Emerging Microbial Threats) project. The work demonstrates how city-wide microbiome sensor networks in homes, hospitals, and commercial buildings can predict and manage allergy outcomes and pathogen transmission.

Dashboard URL after GitHub Pages is enabled for this repo:
`https://ssun6.github.io/claudePremierVisualizations/visualizations/dashboard.html`

## What's in this repository

### Manuscript (`manuscript/`)

- **microbiome_allergy_simulation.pdf** — The compiled paper describing the full simulation framework, statistical analysis pipeline, and results. Covers the AR(1) microbiome dynamics model calibrated from Hill et al. (2026), the AllergyANN neural network (R²=0.787), and power/sensitivity analysis across univariate, mixed-effects, and mediation approaches.
- **manuscript.tex** — LaTeX source for the paper.

### Interactive 3D Visualizations (`visualizations/`)

All HTML files are self-contained and run offline by opening directly in a browser (file:// protocol). No server or internet connection required.

If this repository is published with GitHub Pages, the main dashboard will be available at:
`https://ssun6.github.io/claudePremierVisualizations/visualizations/dashboard.html`

- **dashboard.html** — The main operations console. A full 3D city (Plaza Midwood, Charlotte NC) with 4,000 households, 4 hospitals, and 18 downtown skyscrapers. Features include:
  - ~600 active "subscriber" households with simulated 90-day sensor data
  - Double-click any subscriber house, hospital, or skyscraper to enter a 3D interior view with chart screens showing taxa trends, allergy scores, humidity, temperature, and prediction error
  - Labeled sensor bots patrolling each interior (Sensing Bot, UV Sterilizer Bot, Air Quality Bot, etc.)
  - Color overlay modes (allergy, humidity, temperature, PM2.5, prediction error, taxon abundance)
  - Floating warning indicators above high-value houses (clickable to inspect)
  - PCA embedding view, predicted-vs-actual scatter, model configuration editor
  - Real Claude AI chat integration (requires API key)
  - Arrow key panning, mouse orbit, scroll zoom

- **worldView.html** — City-scale overview scene showing the intelligent microbiome management concept across hospital, residential, and commercial buildings with 10+ robot types and a legend system.

- **hospital.html** — Hospital ICU narrative scene. P-trap biofilm detection, CRE pathogen visualization, probiotic competitive exclusion, 3 roomba bots, 3 pipe robots, and an AI communication hub.

- **basement.html** — Residential basement narrative scene. Fungal mold colony detection and remediation with patrol/spray bots, spore/VOC particle systems, and an intervention workflow.

- **FIGURE_INSTRUCTIONS.md** — Detailed instructions for generating publication figures from the visualizations.
- **basementSchematic.png**, **hospitalSchematic.png** — Reference schematics.

### Simulation & Analysis Scripts (`simulation/`)

All R scripts require `module load R/4.5.1`. Python scripts use `/usr/bin/python3`.

- **sim_microbiome_allergies.R** — Core simulation engine. Generates 4,000 households × 90 days of microbiome, environmental, and allergy data using AR(1) dynamics calibrated from Hill et al. (2026). Defines 5 causal taxa (10/8/6/4/2% effect sizes) and confounded taxa coupled to humidity, temperature, and PM2.5.
- **univariate_linear_models.R** — Fits per-taxon linear models across households. Produces volcano plots, FDR-ranked significance, and coefficient comparisons.
- **mixed_effects_models.R** — Fits mixed-effects models with household random intercepts. Compares sensitivity and false positive rates against univariate approach.
- **power_univariate.R** — Power analysis sweeping number of households and sampling days. Shows that more households improve sensitivity while more days reduce false positives, and that BH FDR correction fails (65–90% observed FDR).
- **mediation_analysis.R** — Mediation analysis testing whether environmental variables mediate taxon–allergy relationships.
- **ann_analysis.py** — Trains the AllergyANN neural network (105→128→64→32→16→1, 24,833 parameters). Produces training loss curves, PCA comparison, and predicted-vs-actual scatter.
- **generate_paper.py** — Assembles the LaTeX manuscript and compiles it to PDF. Generates all figure references and statistical summaries programmatically.

### Data (`data/`)

- **univariate_results.csv** — Per-taxon linear model coefficients, p-values, and significance flags.
- **mixed_effects_results.csv** — Mixed-effects model results with household random effects.
- **power_results.csv**, **power_univariate_results.csv** — Power analysis results across parameter sweeps.
- **mediation_power_results.csv** — Mediation analysis power results.
- **ann_results.json** — AllergyANN training metrics, final R², and architecture details.

### Figures (`figures/`)

Publication-quality PNG figures generated by the analysis scripts. Includes simulation diagnostics, volcano plots, power curves, ANN training/validation plots, and mediation tradeoff analyses.

### Supporting Files

- **lib/three-bundle.js** — Three.js r163 + OrbitControls + CSS2DRenderer/CSS2DObject bundled as a single IIFE script for offline use.
- **fonts/** — DM Sans and JetBrains Mono webfonts (woff2).
- **img/** — PreMiEr consortium logo.

---

## Instructions for a Git Agent to Recreate Everything

Follow these steps in order. Each step depends on the outputs of previous steps.

### 1. Environment Setup

```bash
module load R/4.5.1
# Python 3.9+ must be available at /usr/bin/python3
# R packages needed: lme4, mediation, ggplot2, dplyr, glmnet
# Python packages needed: numpy, torch, matplotlib, json
# LaTeX (pdflatex) is needed for manuscript compilation but may not be available on all systems
```

### 2. Run the Core Simulation

```bash
cd simulation
Rscript sim_microbiome_allergies.R
```

This produces the base simulated dataset (households × days × taxa × environmental variables × allergy scores). Output CSV files go to `../data/`. Output PNG figures go to `../figures/`.

### 3. Run Statistical Analyses (in order)

```bash
Rscript univariate_linear_models.R       # produces univariate_results.csv + volcano/coefficient PNGs
Rscript mixed_effects_models.R           # produces mixed_effects_results.csv + comparison PNGs
Rscript power_univariate.R               # produces power_univariate_results.csv + power curve PNGs
Rscript mediation_analysis.R             # produces mediation_power_results.csv + mediation PNGs
```

Note: `power_univariate.R` and `mediation_analysis.R` are computationally intensive and produce log files.

### 4. Train the Neural Network

```bash
python3 ann_analysis.py
```

Trains the AllergyANN model (105→128→64→32→16→1). Produces `../data/ann_results.json` and training/validation PNGs in `../figures/`.

### 5. Generate the Manuscript PDF

```bash
python3 generate_paper.py
```

This assembles `../manuscript/manuscript.tex` from the simulation results and compiles it to `../manuscript/microbiome_allergy_simulation.pdf`. Requires `pdflatex` in PATH.

### 6. Visualizations

The HTML files in `visualizations/` are self-contained and need no build step. They load `../lib/three-bundle.js` for 3D rendering. To view them:

- Open any `.html` file directly in a modern browser (Chrome, Firefox, Edge)
- Works via `file://` protocol — no web server needed
- `dashboard.html` is the main application; the others are standalone narrative scenes

### 7. Key Technical Notes

- **Three.js**: All visualizations use Three.js r163 bundled as a non-module IIFE (`lib/three-bundle.js`). This avoids ES module import issues over `file://` protocol.
- **NEVER** use `Object.assign(new THREE.Mesh(...), { position: ... })` — Three.js `position` is a read-only Vector3. Always use `.position.set(x, y, z)`.
- **R quirk**: `cv.glmnet` requires explicit `foldid` argument (the `nfolds=` parameter causes dimension errors).
- **R quirk**: Base R `reshape()` is unreliable — use `do.call(rbind, lapply(...))` instead.
- **Dashboard data**: All household/sensor data is generated procedurally in JavaScript at page load. No external data files are needed for the visualizations.
- **Claude API**: `dashboard.html` supports optional real-time Claude AI chat. Users enter their own API key (stored in sessionStorage only, never persisted). Uses the `anthropic-dangerous-direct-browser-access: true` header for browser-side calls.
