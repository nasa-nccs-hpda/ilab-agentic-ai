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
| `notebooks/3l_metrics_thermal_diff_fix.ipynb` | Canonical metrics-generation notebook (MODIS-equivalent, PACE hyperspectral, AltSort phenology-sorted, thermal, snow-aware metrics). Includes the fix described in `knowledge/troubleshooting/scale-thermal-diff-regression.md`. |
| `notebooks/6h_pace_train_noprefix_legacy.ipynb` | Tabular ("legacy") XGBoost training + Monte Carlo feature selection, without AlphaEarth. Reflects the corrected 70/15/15 split (`knowledge/troubleshooting/test-set-leakage-in-monte-carlo-selection.md`). |
| `notebooks/6zg_pace_train_legacy_alpha.ipynb` | Same as above, with AlphaEarth embeddings added as features. |
| `notebooks/6g_pace_train_chips.ipynb` | Chip-tiled XGBoost training (spatial context via fixed-size image chips), without AlphaEarth. |
| `notebooks/6zh_pace_train_chips_alpha.ipynb` | Same as above, with AlphaEarth embeddings added. |
| `notebooks/11_test_holdout_r2_all_models.ipynb` | The three-model (XGBoost / Spatial-CNN / Pixel-Transformer) true 15%-holdout comparison; see `knowledge/models/three-model-comparison.md`. |
| `notebooks/7g_inference_C6_xgboost_legacy_subset.ipynb` | Inference + comparison against MODIS VCF Collection 6, run on a small tile subset with isolated output. |

See `knowledge/overview/project-overview.md` for how these fit into the full
notebook lineage (`2`-series composites through `9`/`10` super-resolution
and spatial-comparison notebooks, not included here).
