#!/usr/bin/env python3
"""
ANN analysis: Train neural network to predict allergy from taxa + environment.
Compare PCA on ANN embedding vs PCA on raw features for correlation with allergy.
80/20 household-level train/test split.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

np.random.seed(42)
torch.manual_seed(42)

OUTDIR = os.path.dirname(os.path.abspath(__file__))

###############################################################################
# 1. SIMULATION (matching sim_microbiome_allergies.R)
###############################################################################

def simulate_study(n_households=100, n_persons_per=3, n_days=90, n_taxa=100,
                   n_causal=5, causal_effects=None, env_effect_humidity=0.03,
                   env_effect_pm25=0.05, noise_sd=0.15, person_sd=0.30,
                   household_sd=0.20, symptom_ar=0.3):
    if causal_effects is None:
        causal_effects = np.array([0.10, 0.08, 0.06, 0.04, 0.02])

    taxon_names = [f"taxon_{i+1:03d}" for i in range(n_taxa)]
    causal_idx = list(range(n_causal))

    # Taxon properties
    taxon_mean_log = np.random.normal(-3, 1.5, n_taxa)
    taxon_cv = 0.05 + 0.20 * np.random.beta(2, 3, n_taxa)
    taxon_ar = np.clip(1 - 3 * taxon_cv, 0.05, 0.95)
    taxon_innov_sd = taxon_cv * np.sqrt(1 - taxon_ar**2)

    # Environment-linked taxa (0-indexed)
    humidity_linked = {0, 1, 9, 14, 19}
    temp_linked = {2, 3, 10, 15, 24}
    pm25_linked = {4, 11, 16, 29, 34}
    env_coupling = 0.3

    rows = []
    for h in range(n_households):
        day_vec = np.arange(n_days)
        season_phase = np.random.uniform(0, 2 * np.pi)

        # Temperature
        temp_base = 20 + 5 * np.sin(2 * np.pi * day_vec / 365 + season_phase)
        temp_noise = np.zeros(n_days)
        temp_noise[0] = np.random.normal(0, 1.5)
        for t in range(1, n_days):
            temp_noise[t] = 0.7 * temp_noise[t-1] + np.random.normal(0, 1.5)
        temp = temp_base + temp_noise

        # Humidity
        humid_base = 50 + 10 * np.sin(2 * np.pi * day_vec / 365 + season_phase + np.pi/4)
        humid_noise = np.zeros(n_days)
        humid_noise[0] = np.random.normal(0, 5)
        for t in range(1, n_days):
            humid_noise[t] = 0.6 * humid_noise[t-1] + np.random.normal(0, 5)
        humidity = np.clip(humid_base + 0.5 * (temp - np.mean(temp)) + humid_noise, 20, 90)

        # PM2.5
        pm25_noise = np.zeros(n_days)
        pm25_noise[0] = np.random.normal(0, 3)
        for t in range(1, n_days):
            pm25_noise[t] = 0.5 * pm25_noise[t-1] + np.random.normal(0, 3)
        pm25_spikes = (np.random.binomial(1, 0.05, n_days) *
                       np.random.exponential(20, n_days))
        pm25 = np.maximum(2, 10 + pm25_noise + pm25_spikes)

        # CO2
        co2_noise = np.zeros(n_days)
        co2_noise[0] = np.random.normal(0, 50)
        for t in range(1, n_days):
            co2_noise[t] = 0.4 * co2_noise[t-1] + np.random.normal(0, 50)
        co2 = np.maximum(400, 600 + 200 * np.sin(2 * np.pi * day_vec / 7) + co2_noise)

        # Fungal
        fungal = np.maximum(0, 100 + 2 * (humidity - 50) +
                            50 * np.sin(2 * np.pi * day_vec / 365 + season_phase) +
                            np.random.normal(0, 20, n_days))

        # Taxa AR(1)
        hh_shift = np.random.normal(0, 0.3, n_taxa)
        taxa = np.zeros((n_days, n_taxa))
        for j in range(n_taxa):
            taxa[0, j] = taxon_mean_log[j] + hh_shift[j] + np.random.normal(0, taxon_cv[j])
            for t in range(1, n_days):
                taxa[t, j] = (taxon_mean_log[j] + hh_shift[j] +
                              taxon_ar[j] * (taxa[t-1, j] - taxon_mean_log[j] - hh_shift[j]) +
                              np.random.normal(0, taxon_innov_sd[j]))
                humid_z = (humidity[t] - 50) / 15
                temp_z = (temp[t] - 20) / 5
                pm25_z = (pm25[t] - 10) / 5
                if j in humidity_linked:
                    taxa[t, j] += env_coupling * humid_z * taxon_innov_sd[j]
                if j in temp_linked:
                    taxa[t, j] += env_coupling * temp_z * taxon_innov_sd[j]
                if j in pm25_linked:
                    taxa[t, j] += env_coupling * pm25_z * taxon_innov_sd[j]

        # Convert to relative abundance (softmax-like on exp scale)
        taxa_abs = np.exp(taxa)
        taxa_rel = taxa_abs / taxa_abs.sum(axis=1, keepdims=True)

        # Allergy per person
        for p in range(n_persons_per):
            person_baseline = np.random.normal(3, person_sd)
            hh_effect = np.random.normal(0, household_sd)
            allergy = np.zeros(n_days)
            allergy[0] = person_baseline + hh_effect

            for t in range(1, n_days):
                taxa_signal = np.sum(causal_effects * taxa[t, :n_causal])
                env_signal = (env_effect_humidity * (humidity[t] - 50) / 15 +
                              env_effect_pm25 * (pm25[t] - 10) / 5)
                allergy[t] = (person_baseline + hh_effect +
                              symptom_ar * (allergy[t-1] - person_baseline - hh_effect) +
                              taxa_signal + env_signal +
                              np.random.normal(0, noise_sd))

            for t in range(n_days):
                row = {
                    'household': h, 'person': p, 'day': t,
                    'allergy': allergy[t],
                    'temperature': temp[t], 'humidity': humidity[t],
                    'pm25': pm25[t], 'co2': co2[t], 'fungal': fungal[t],
                }
                for j in range(n_taxa):
                    row[taxon_names[j]] = taxa_rel[t, j]
                rows.append(row)

    return rows, taxon_names, causal_idx

###############################################################################
# 2. ANN MODEL
###############################################################################

class AllergyANN(nn.Module):
    def __init__(self, n_input, n_embedding=32, dropout=0.2):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_input, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_embedding),
            nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(n_embedding, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        emb = self.encoder(x)
        return self.head(emb)

    def get_embedding(self, x):
        with torch.no_grad():
            return self.encoder(x).numpy()

###############################################################################
# 3. MAIN ANALYSIS
###############################################################################

def main():
    print("=== Simulating data (500 households x 3 persons x 90 days) ===")
    rows, taxon_names, causal_idx = simulate_study(n_households=500)

    # Build arrays
    n = len(rows)
    n_taxa = len(taxon_names)
    env_cols = ['temperature', 'humidity', 'pm25', 'co2', 'fungal']
    n_features = n_taxa + len(env_cols)

    X = np.zeros((n, n_features))
    y = np.zeros(n)
    households = np.zeros(n, dtype=int)
    persons = np.zeros(n, dtype=int)

    for i, row in enumerate(rows):
        for j, tn in enumerate(taxon_names):
            X[i, j] = row[tn]
        for j, ec in enumerate(env_cols):
            X[i, n_taxa + j] = row[ec]
        y[i] = row['allergy']
        households[i] = row['household']
        persons[i] = row['household'] * 10 + row['person']  # unique person ID

    print(f"Data: {n} rows, {n_features} features")

    # Person-level demeaning (remove between-person variation)
    # This lets the ANN focus on within-person temporal associations
    unique_persons = np.unique(persons)
    X_demeaned = X.copy()
    y_demeaned = y.copy()
    person_y_means = {}
    person_X_means = {}
    for pid in unique_persons:
        mask = persons == pid
        person_X_means[pid] = X[mask].mean(axis=0)
        person_y_means[pid] = y[mask].mean()
        X_demeaned[mask] -= person_X_means[pid]
        y_demeaned[mask] -= person_y_means[pid]

    print(f"Person-level demeaning applied ({len(unique_persons)} persons)")
    print(f"Allergy SD: raw={y.std():.3f}, demeaned={y_demeaned.std():.3f}")

    # 80/20 household split
    unique_hh = np.unique(households)
    np.random.shuffle(unique_hh)
    split = int(0.8 * len(unique_hh))
    train_hh = set(unique_hh[:split])
    test_hh = set(unique_hh[split:])

    train_mask = np.array([h in train_hh for h in households])
    test_mask = ~train_mask

    print(f"Train: {train_mask.sum()} rows ({len(train_hh)} HH), "
          f"Test: {test_mask.sum()} rows ({len(test_hh)} HH)")

    # Scale demeaned features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_demeaned[train_mask])
    X_test = scaler.transform(X_demeaned[test_mask])

    y_scaler = StandardScaler()
    y_train = y_scaler.fit_transform(y_demeaned[train_mask].reshape(-1, 1)).ravel()
    y_test_demeaned = y_demeaned[test_mask]
    y_test_raw = y[test_mask]

    # Also keep raw (non-demeaned) scaled features for PCA comparison
    scaler_raw = StandardScaler()
    X_raw_scaled = scaler_raw.fit_transform(X)

    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
    X_test_t = torch.FloatTensor(X_test)

    # Train ANN
    print("\n=== Training ANN ===")
    model = AllergyANN(n_features, n_embedding=32, dropout=0.2)
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    criterion = nn.MSELoss()

    # Scale test y for validation loss (demeaned)
    y_test_scaled = y_scaler.transform(y_test_demeaned.reshape(-1, 1)).ravel()
    y_test_t = torch.FloatTensor(y_test_scaled).unsqueeze(1)

    # Mini-batch training
    batch_size = 256
    n_epochs = 300
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    best_state = None
    patience_counter = 0

    for epoch in range(n_epochs):
        model.train()
        perm = torch.randperm(X_train_t.shape[0])
        epoch_loss = 0
        n_batches = 0
        for i in range(0, X_train_t.shape[0], batch_size):
            idx = perm[i:i+batch_size]
            xb, yb = X_train_t[idx], y_train_t[idx]
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        train_losses.append(epoch_loss / n_batches)

        # Validation loss
        model.eval()
        with torch.no_grad():
            val_pred = model(X_test_t)
            val_loss = criterion(val_pred, y_test_t).item()
        val_losses.append(val_loss)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1}: train={train_losses[-1]:.4f}, val={val_loss:.4f}, lr={optimizer.param_groups[0]['lr']:.6f}")

        if patience_counter >= 30:
            print(f"  Early stopping at epoch {epoch+1}")
            break

    # Restore best model
    model.load_state_dict(best_state)
    print(f"  Best validation loss: {best_val_loss:.4f}")

    # Evaluate on test set
    model.eval()
    with torch.no_grad():
        y_pred_scaled = model(X_test_t).numpy().ravel()
    y_pred_demeaned = y_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

    # Demeaned test metrics (within-person prediction)
    test_r_dm = np.corrcoef(y_test_demeaned, y_pred_demeaned)[0, 1]
    test_r2_dm = test_r_dm**2
    test_mse_dm = np.mean((y_test_demeaned - y_pred_demeaned)**2)
    test_mae_dm = np.mean(np.abs(y_test_demeaned - y_pred_demeaned))
    print(f"\nDemeaned test: R = {test_r_dm:.4f}, R² = {test_r2_dm:.4f}")
    print(f"Demeaned test: MSE = {test_mse_dm:.4f}, MAE = {test_mae_dm:.4f}")

    # Add back person means for raw-scale metrics
    test_persons = persons[test_mask]
    y_pred_raw = y_pred_demeaned.copy()
    for i, pid in enumerate(test_persons):
        y_pred_raw[i] += person_y_means[pid]

    test_r = np.corrcoef(y_test_raw, y_pred_raw)[0, 1]
    test_r2 = test_r**2
    test_mse = np.mean((y_test_raw - y_pred_raw)**2)
    test_mae = np.mean(np.abs(y_test_raw - y_pred_raw))
    print(f"\nRaw-scale test: R = {test_r:.4f}, R² = {test_r2:.4f}")
    print(f"Raw-scale test: MSE = {test_mse:.4f}, MAE = {test_mae:.4f}")

    # =========================================================================
    # 4. PCA COMPARISON: Embedding vs Raw features
    # =========================================================================
    print("\n=== PCA Comparison ===")

    # Get embeddings for ALL data (demeaned input)
    X_all_dm_scaled = scaler.transform(X_demeaned)
    X_all_dm_t = torch.FloatTensor(X_all_dm_scaled)
    embeddings = model.get_embedding(X_all_dm_t)  # (n, 32)

    # PCA on raw features (non-demeaned, to represent what you'd get without the ANN)
    pca_raw = PCA(n_components=10)
    raw_pcs = pca_raw.fit_transform(X_raw_scaled)

    # PCA on embeddings
    pca_emb = PCA(n_components=10)
    emb_pcs = pca_emb.fit_transform(embeddings)

    # Correlate each PC with demeaned allergy (the signal the ANN was trained on)
    print("\nCorrelation with demeaned allergy (within-person variation):")
    print("PC  | Raw r    | Raw r²   | Emb r    | Emb r²")
    print("----|----------|----------|----------|--------")
    raw_cors = []
    emb_cors = []
    for pc in range(10):
        r_raw = np.corrcoef(y_demeaned, raw_pcs[:, pc])[0, 1]
        r_emb = np.corrcoef(y_demeaned, emb_pcs[:, pc])[0, 1]
        raw_cors.append(r_raw)
        emb_cors.append(r_emb)
        print(f"PC{pc+1:2d}| {r_raw:+.4f}  | {r_raw**2:.4f}  | {r_emb:+.4f}  | {r_emb**2:.4f}")

    # Best single PC correlation
    best_raw_pc = np.argmax([abs(r) for r in raw_cors])
    best_emb_pc = np.argmax([abs(r) for r in emb_cors])
    print(f"\nBest raw PC: PC{best_raw_pc+1} (r={raw_cors[best_raw_pc]:+.4f})")
    print(f"Best emb PC: PC{best_emb_pc+1} (r={emb_cors[best_emb_pc]:+.4f})")

    # Multiple regression: top 5 PCs → demeaned allergy (R² comparison)
    # Fit on TRAIN data only, evaluate on TEST data
    from sklearn.linear_model import LinearRegression

    # Train-set PCs
    raw_pcs_train = raw_pcs[train_mask]
    emb_pcs_train = emb_pcs[train_mask]
    y_dm_train = y_demeaned[train_mask]

    lr_raw = LinearRegression().fit(raw_pcs_train[:, :5], y_dm_train)
    r2_raw_5pc = lr_raw.score(raw_pcs_train[:, :5], y_dm_train)

    lr_emb = LinearRegression().fit(emb_pcs_train[:, :5], y_dm_train)
    r2_emb_5pc = lr_emb.score(emb_pcs_train[:, :5], y_dm_train)

    print(f"\nTrain R² from top 5 PCs → demeaned allergy:")
    print(f"  Raw features: {r2_raw_5pc:.4f}")
    print(f"  ANN embedding: {r2_emb_5pc:.4f}")

    # Test-set evaluation
    raw_pcs_test = raw_pcs[test_mask]
    emb_pcs_test = emb_pcs[test_mask]

    r2_raw_test = lr_raw.score(raw_pcs_test[:, :5], y_test_demeaned)
    r2_emb_test = lr_emb.score(emb_pcs_test[:, :5], y_test_demeaned)

    print(f"\nTest R² from top 5 PCs → demeaned allergy:")
    print(f"  Raw features: {r2_raw_test:.4f}")
    print(f"  ANN embedding: {r2_emb_test:.4f}")

    # Variance explained by PCA
    print(f"\nVariance explained (PCA):")
    print(f"  Raw top 5: {pca_raw.explained_variance_ratio_[:5].sum():.3f}")
    print(f"  Emb top 5: {pca_emb.explained_variance_ratio_[:5].sum():.3f}")

    # =========================================================================
    # 5. GENERATE FIGURES
    # =========================================================================
    print("\n=== Generating figures ===")

    # Fig 1: Training + validation loss curve
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(train_losses, label='Train')
    ax.plot(val_losses, label='Validation')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss (MSE)')
    ax.set_title('ANN Training and Validation Loss')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'ann_training_loss.png'), dpi=150)
    plt.close()

    # Fig 2: Predicted vs actual (test set, raw scale)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_test_raw, y_pred_raw, alpha=0.1, s=5)
    lims = [min(y_test_raw.min(), y_pred_raw.min()), max(y_test_raw.max(), y_pred_raw.max())]
    ax.plot(lims, lims, 'r--', linewidth=1)
    ax.set_xlabel('Actual Allergy Score')
    ax.set_ylabel('Predicted Allergy Score')
    ax.set_title(f'ANN Test Set: R²={test_r2:.3f}, MAE={test_mae:.3f}')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'ann_pred_vs_actual.png'), dpi=150)
    plt.close()

    # Fig 3: PCA comparison - bar chart of |r| with allergy for each PC
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    pcs = np.arange(1, 11)

    axes[0].bar(pcs, [abs(r) for r in raw_cors], color='steelblue', alpha=0.8)
    axes[0].set_xlabel('Principal Component')
    axes[0].set_ylabel('|Correlation with Allergy|')
    axes[0].set_title('PCA on Raw Features')
    axes[0].set_ylim(0, max(max(abs(r) for r in raw_cors), max(abs(r) for r in emb_cors)) * 1.15)
    axes[0].set_xticks(pcs)

    axes[1].bar(pcs, [abs(r) for r in emb_cors], color='darkorange', alpha=0.8)
    axes[1].set_xlabel('Principal Component')
    axes[1].set_ylabel('|Correlation with Allergy|')
    axes[1].set_title('PCA on ANN Embedding')
    axes[1].set_ylim(axes[0].get_ylim())
    axes[1].set_xticks(pcs)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'ann_pca_comparison.png'), dpi=150)
    plt.close()

    # Fig 4: Embedding PCA scatter (PC1 vs PC2 colored by allergy)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    vmin, vmax = np.percentile(y_demeaned, [5, 95])

    sc = axes[0].scatter(raw_pcs[:, 0], raw_pcs[:, 1], c=y_demeaned, cmap='RdYlBu_r',
                         alpha=0.05, s=3, vmin=vmin, vmax=vmax)
    axes[0].set_xlabel(f'PC1 ({pca_raw.explained_variance_ratio_[0]:.1%})')
    axes[0].set_ylabel(f'PC2 ({pca_raw.explained_variance_ratio_[1]:.1%})')
    axes[0].set_title('Raw Feature PCA')

    sc2 = axes[1].scatter(emb_pcs[:, 0], emb_pcs[:, 1], c=y_demeaned, cmap='RdYlBu_r',
                          alpha=0.05, s=3, vmin=vmin, vmax=vmax)
    axes[1].set_xlabel(f'PC1 ({pca_emb.explained_variance_ratio_[0]:.1%})')
    axes[1].set_ylabel(f'PC2 ({pca_emb.explained_variance_ratio_[1]:.1%})')
    axes[1].set_title('ANN Embedding PCA')

    fig.colorbar(sc2, ax=axes, label='Demeaned Allergy Score', shrink=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'ann_pca_scatter.png'), dpi=150)
    plt.close()

    # Save results for PDF generation
    results = {
        'n_households': 500, 'n_persons': 3, 'n_days': 90,
        'n_train_hh': len(train_hh), 'n_test_hh': len(test_hh),
        'n_train_rows': int(train_mask.sum()), 'n_test_rows': int(test_mask.sum()),
        'n_features': n_features, 'n_embedding': 32,
        'test_r': float(test_r), 'test_r2': float(test_r2),
        'test_mse': float(test_mse), 'test_mae': float(test_mae),
        'test_r_demeaned': float(test_r_dm), 'test_r2_demeaned': float(test_r2_dm),
        'raw_pc_cors': [float(r) for r in raw_cors],
        'emb_pc_cors': [float(r) for r in emb_cors],
        'r2_raw_5pc': float(r2_raw_5pc), 'r2_emb_5pc': float(r2_emb_5pc),
        'r2_raw_test': float(r2_raw_test), 'r2_emb_test': float(r2_emb_test),
        'raw_var_explained_5': float(pca_raw.explained_variance_ratio_[:5].sum()),
        'emb_var_explained_5': float(pca_emb.explained_variance_ratio_[:5].sum()),
        'raw_var_explained': [float(v) for v in pca_raw.explained_variance_ratio_[:10]],
        'emb_var_explained': [float(v) for v in pca_emb.explained_variance_ratio_[:10]],
        'final_train_loss': float(train_losses[-1]),
    }

    with open(os.path.join(OUTDIR, 'ann_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to ann_results.json")
    print("Figures: ann_training_loss.png, ann_pred_vs_actual.png, "
          "ann_pca_comparison.png, ann_pca_scatter.png")
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
