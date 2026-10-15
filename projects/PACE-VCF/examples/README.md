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

### Metrics v4 (current, October 2026)

| Notebook | What it shows |
| --- | --- |
| `notebooks/3n_metrics_v4_no_duplicates.ipynb` | v4 metrics generation for one tile into a scratch folder (generated from `scripts/run_metrics_generation_v4.py` by `scripts/make_notebook_3n.py`): rank-based amplitude and median metrics, duplicate removal, renames, and checks. See `knowledge/algorithms/metrics-v4-definitions-and-duplicate-bands.md`. |
| `notebooks/6j_pace_train_chips_v4.ipynb` | Chip-based XGBoost + Monte Carlo feature selection on the v4 training chips (5,000 trials). See the v4 section of `knowledge/models/xgboost-monte-carlo-feature-selection.md`. |
| `notebooks/13_v4_final_model_tile_comparison.ipynb` | Full-tile comparison of the three v4 final models against MODIS VCF (per-tile maps and scatter plots; pooled scores on pixels with real inputs; v4 vs v3 and v2 on identical pixels). See `knowledge/models/three-model-comparison.md`. |

### Shelved-era (v2) notebooks

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
| `notebooks/9a_superresolution_test.ipynb` | Super-resolution via guided filter and residual/ratio injection (2 km -> 250 m). See `knowledge/models/super-resolution-2km-to-250m.md` for results -- neither method recovers real detail. |
| `notebooks/9b_superresolution_alphaearth_regression.ipynb` | Super-resolution via AlphaEarth-embedding regression -- no same-tile guide needed. The one super-resolution method that visibly recovers real fine-scale detail; see the same results doc. |
| `notebooks/11_test_holdout_r2_all_models.ipynb` | The three-model (XGBoost / Spatial-CNN / Pixel-Transformer) true 15%-holdout comparison; see `knowledge/models/three-model-comparison.md`. |

See `knowledge/overview/project-overview.md` for how these fit into the full
notebook lineage (the `10` spatial-comparison notebook is not included here).

## Other data

- `feature_importance.txt` -- top-30/top-50 feature importance rankings
  (rank, feature, model, feature-source style, band/index) across all five
  models compared in this project (`C6-Modis_Legacy`, `XGBoost_Legacy`,
  `XGBoost_Chipped`, the CNN/MLP/Transformer chipped models). This is the
  underlying data behind `notebooks/8a_feature_comparison.ipynb`'s bump
  chart -- useful on its own if you want the raw rankings without
  regenerating the plot.
- `feature_importance_v4_consensus.txt` -- the same format for the v4 final
  models: the C6-Modis_Legacy top 30, then each model's consensus top 50 from
  the five-seed study (`knowledge/models/multi-seed-ranking-stability.md`).
  Style is MODIS or PACE (PACE = PACE_Metrics + PACE_AltSort_Metrics).
  Tab-separated, CRLF line endings.

## Scripts (metrics v4)

`scripts/` holds the batch launchers and helpers used for the v4 run, as
they were on NCCS Explore. They will not run elsewhere: they use internal
paths, a project virtual environment, Slurm on NCCS, and call a colleague's
non-public chip-training package in place (that package is **not** included).
Every launcher makes a new timestamped output folder and refuses to overwrite.
The run order and checks are in `skills/run-pace-vcf-pipeline/`.

| Script | Purpose |
| --- | --- |
| `run_metrics_generation_v4.py`, `test_metrics_v4.py` | v4 metrics for one tile, and unit tests for the new rank-based metrics |
| `launch_metrics_v4.sh`, `submit_metrics_v4.sbatch` | v4 metrics for all 291 tiles as independent 1-core CPU jobs (`status` mode to check) |
| `make_notebook_3n.py` | builds notebook 3n from the v4 metrics script |
| `chips_v3/version_config.sh` | maps `METRICS_VERSION` (v3 / v4) to chip run, model folder, stack folder and band count; read by every launcher |
| `chips_v3/launch_chips_v3.sh`, `submit_chips_v3.sbatch`, `tile_indices.py`, `compare_chips.py` | training chips with the colleague's code (tiles by name), and the chip check |
| `chips_v3/launch_training_v3.sh`, `train_model_v3.sbatch` | all-band training, three models, one GPU job each |
| `chips_v3/launch_xai_v3.sh` | fuller integrated-gradients XAI for the neural models |
| `chips_v3/launch_sweep_v3.sh`, `train_sweep_v3.sbatch`, `make_topn_lists.py` | band-count sweep |
| `chips_v3/launch_seed_study_v3.sh`, `train_seed_v3.sbatch`, `train_init_seed.py`, `combine_seed_rankings.py` | multi-seed study (model seed varies, split fixed) and consensus rankings |
| `chips_v3/launch_final_v3.sh`, `train_final_v3.sbatch` | final models (`CONSENSUS_DIR` = use the seed-study consensus lists) |
| `chips_v3/launch_cnn_check_v3.sh` | the Spatial-CNN band-list check |
| `chips_v3/launch_style_test_v3.sh` | MODIS-style only vs PACE-style only |
| `chips_v3/eval_chip_models.py` | per-layer R² / RMSE for neural checkpoints on the val/test chips |
| `launch_stacks_v4.sh`, `submit_stacks_v3.sbatch` | full-tile input stacks (475 bands, chip band order) |
| `run_multi_model_inference.py`, `launch_inference_v3.sh`, `submit_inference_v3.sbatch` | global inference; v4 models are `--model all-v4` |
| `plot_band_sweep.py` | band-count sweep figure (`--version v4`) |

File names keep `_v3` from the version they were written for; the metrics
version is a setting, not the file name.
