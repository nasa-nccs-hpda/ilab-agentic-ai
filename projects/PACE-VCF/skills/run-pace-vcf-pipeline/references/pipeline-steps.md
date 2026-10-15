# PACE-VCF pipeline: per-step notes

Read the step you are about to run. Paths and commands are NCCS-internal.

### 1. Metrics -> `PV/output/<tile>/2025/3-Metrics-v4/`

`run_metrics_generation_v4.py` writes three files per tile (MODIS_Metrics,
PACE_Metrics, PACE_AltSort_Metrics; int16, reflectance x10000, index x1000,
REP x10, nodata -10001). Notebook `3n_metrics_v4_no_duplicates.ipynb` runs one
tile into a scratch folder for repeatability. Tests: `test_metrics_v4.py`.
Check: `launch_metrics_v4.sh status` shows 291/291; band counts 298/146/206.

### 2. Chips -> `PV/chip_outputs/metrics_v4/<run>/`

The colleague's chipping code, unchanged except `--input-metrics-subdir`. Tiles are
passed by name (the CLI indexes a sorted inventory that changes as tiles
gain metrics). Check: `$PY chips_v3/compare_chips.py <run> --allow-new-band-list`
must find the same chip IDs and labels as the v2 chips (504 chips, 63 tiles),
one band count, no repeated band names. A zero-tile result is an error.

### 4-6. Training, XAI, sweep -> `PV/models/v4_metrics/chip_models/`

- Settings are the colleague's 2026-09-09 run: 30 epochs, Huber loss, batch 4,
  seed-7 70/15/15 **chip-level** split (353/76/75 chips); XGBoost 500 trees,
  depth 10, lr 0.1, early stop 30, GPU.
- Training writes a 5-tile map check, so step 3's stacks must exist first.
- Neural models only log pooled RMSE; score tree cover with
  `chips_v3/eval_chip_models.py` in a GPU job (the launchers chain this).
- Training-time XAI (8 chips, 8 steps) is noisy; step 5 uses all 76 val chips,
  64 steps, best checkpoint. The transformer needs IG internal batch 4 on a
  32 GB V100.
- The sweep retrains each model on its own top 10/25/50/100/200 bands
  (`make_topn_lists.py`); plot with
  `presentations/plot_band_sweep.py --version v4`.
- **The owner picks the band count** from the sweep (v4: 100 for all three).

### 7. Multi-seed study

One training run gives one sample of a model's band ranking. The colleague's neural
CLI ties the split seed and the model seed together, so
`chips_v3/train_init_seed.py` keeps split seed 7 and varies only the model
seed; the XGBoost CLI already separates `--split-seed` and `--seed`. The
study trains each model on all bands at seeds 11, 23, 37, 41; the all-band
run is the fifth seed. `combine_seed_rankings.py` writes per-band stability,
consensus top-50/100 lists (by mean rank), seed overlap and accuracy spread
to `<seeds_dir>/combined/`.

### 8. Final models

Each model on its consensus top N. **Check each final against the sweep and
the seed spread before using it.** In v4 the CNN final came out 0.7 RMSE
worse than expected; `chips_v3/launch_cnn_check_v3.sh` (lean retrains at
two more seeds via `train_sweep_v3.sbatch INIT_SEED=`) showed it was an
unlucky draw, and the owner chose the run that was best **on validation**. Choose
among runs on validation, never on test.

### 9-10. Stacks and inference -> `PV/multi_model_inference/<model>/`

- A stack is `input_stack_2km.tif` per tile: every band except
  `^(Unsorted|QA_)`, in chip order, plus labels. Check all 291 match the
  chips' band names and order (header read, seconds).
- Models are registered in `run_multi_model_inference.py` (`MODELS`, group
  names like `all-v4`); each entry names its experiment dir, checkpoint,
  exclude-pattern file and stack root. After adding entries, check that each
  pattern keeps exactly its N bands from a stack.
- Inference skips finished tiles, so relaunching only fills gaps.

### 11. Comparison

- Notebook 13: full-tile comparison against MOD44B and earlier versions.
  Mask pixels whose `_raw_chip_predictions/<model>/<tile>/imputed_feature_fraction.tif`
  > 0.5 -- the colleague's inference median-fills missing inputs, and unmasked
  fill pixels swamp the score.
- Notebook 8b: feature analysis from the top-50 text files
  (`feature_importance_v4_consensus.txt` for v4; tab-separated, CRLF,
  columns Rank / Feature / Model / Style (MODIS or PACE) / Band/Index, with
  the C6-Modis_Legacy block kept).

## Testing a launcher without submitting

Copy the launcher and `version_config.sh` to the scratchpad, point
`MODELS_BASE` at a scratch folder, symlink the real input runs into it, and
put a fake `sbatch` first on `PATH` that logs its arguments and prints a job
ID. Run it, then check the folder, metadata, lists and logged sbatch lines.
Also test the refusals (wrong version, bad paths). This caught real bugs
(e.g. a silent `set -e` exit when no run folder existed).

