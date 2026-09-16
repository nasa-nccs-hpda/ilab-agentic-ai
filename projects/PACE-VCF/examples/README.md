# PACE-VCF example notebooks

A curated subset of the private `PACE_VCF` repository's notebooks,
representative of the final workflow. **Cell outputs have been stripped**
to keep the repository small and avoid committing full run logs or
internal file paths as executed output; these notebooks document
methodology and code structure, not a runnable pipeline. They will not
execute outside the original NCCS Explore environment: they reference
`/explore/nobackup/...` paths, restricted datasets (PACE, VIIRS, MODIS VCF),
GPU-specific XGBoost parameters, and (for the model-comparison notebook) a
colleague's separate, non-public package.

| Notebook | What it shows |
| --- | --- |
| `notebooks/1_Data_download.ipynb` | Pipeline entry point: downloads PACE-OCI L3m surface reflectance and VIIRS thermal data via `earthaccess` (interactive Earthdata login, no embedded credentials). |
| `notebooks/1d_check_geo_resolution.ipynb` | Verifies geospatial alignment/resolution consistency between the PACE and MODIS processing grids. |
| `notebooks/2e_composite_aggregate_daily.ipynb` | Most recent composite-generation notebook (32-day composites from daily PACE/VIIRS input). |
| `notebooks/3l_metrics_thermal_diff_fix.ipynb` | Canonical metrics-generation notebook (MODIS-equivalent, PACE hyperspectral, AltSort phenology-sorted, thermal, snow-aware metrics). Includes the fix described in `knowledge/troubleshooting/scale-thermal-diff-regression.md`. |
| `notebooks/4f_metrics_validation_thermal.ipynb` | Most recent metrics-validation notebook; its comparison set is the reference `5c` was reconciled against (see next row). |
| `notebooks/5c_metrics_tif_gen_for_validation.ipynb` | Metrics-TIF generation for validation. Includes the fix described in `knowledge/troubleshooting/orphaned-metrics-list-bug.md`. |
| `notebooks/6h_pace_train_noprefix_legacy.ipynb` | Tabular ("legacy") XGBoost training + Monte Carlo feature selection, without AlphaEarth. Reflects the corrected 70/15/15 split (`knowledge/troubleshooting/test-set-leakage-in-monte-carlo-selection.md`). |
| `notebooks/6zg_pace_train_legacy_alpha.ipynb` | Same as above, with AlphaEarth embeddings added as features. |
| `notebooks/6g_pace_train_chips.ipynb` | Chip-tiled XGBoost training (spatial context via fixed-size image chips), without AlphaEarth. |
| `notebooks/6zh_pace_train_chips_alpha.ipynb` | Same as above, with AlphaEarth embeddings added. |
| `notebooks/7g_inference_C6_xgboost_legacy_subset.ipynb` | Inference + comparison against MODIS VCF Collection 6, run on a small tile subset with isolated output. |
| `notebooks/8a_feature_comparison.ipynb` | Cross-model feature-importance bump chart, filtered to features shared across multiple models. |
| `notebooks/11_test_holdout_r2_all_models.ipynb` | The three-model (XGBoost / Spatial-CNN / Pixel-Transformer) true 15%-holdout comparison; see `knowledge/models/three-model-comparison.md`. |

See `knowledge/overview/project-overview.md` for how these fit into the full
notebook lineage (the `9`/`10` super-resolution and spatial-comparison
notebooks are not included here).

## Other data

- `feature_importance.txt` -- top-30/top-50 feature importance rankings
  (rank, feature, model, feature-source style, band/index) across all five
  models compared in this project (`C6-Modis_Legacy`, `XGBoost_Legacy`,
  `XGBoost_Chipped`, the CNN/MLP/Transformer chipped models). This is the
  underlying data behind `notebooks/8a_feature_comparison.ipynb`'s bump
  chart -- useful on its own if you want the raw rankings without
  regenerating the plot.
