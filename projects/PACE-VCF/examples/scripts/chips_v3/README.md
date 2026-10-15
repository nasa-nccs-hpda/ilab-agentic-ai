# chips_v3: training chips from the v3 metrics

Re-runs AJ Kerr's chipping code (called in place, not copied) on
`3-Metrics-v3`, so the chip models can be retrained on the fixed metrics.

It reproduces his 2026-09-09 `fixed_metrics` chip run, which his current models
were trained on, with one difference: `--input-metrics-subdir 3-Metrics-v3`.
Everything else is copied word for word from that run's `run_metadata.txt`:
same training labels (v5.0.3), same MOD44B labels, same `^(Unsorted|QA_)`
band exclusion. On v3 that exclusion leaves the same 521 bands.

## Overwrite safety

- Every launch creates a **new** timestamped folder under
  `/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/chip_outputs/metrics_v3/`
  and exits if that folder already exists.
- The worker refuses to run if its output path is under `ajkerr1/`, outside
  `chip_outputs/metrics_v3/`, or was not created by the launcher.
- AJ Kerr's code and chips are only read. His v2 chips stay at
  `ajkerr1/PACE_Hyperspectral/chip_outputs/fixed_metrics/`.

## Files

- `launch_chips_v3.sh`: takes tile names, makes the run folder and submits
  the array.
- `submit_chips_v3.sbatch`: one worker per tile. Before starting it checks that
  its array index still points at its tile.
- `tile_indices.py`: turns tile names into array indices using his own
  inventory code.
- `compare_chips.py`: checks new chips against his v2 chips.

## Why tile names, not index numbers

His CLI picks a tile by array index into a sorted list of every tile that has
a folder under `output/` or a training-label file. On 2026-09-09 that list had
69 tiles; once all 291 tiles had metrics it grew, so the same index now points
at a different tile. The 2026-09-30 test run (`test_2026_09_30-09_40_46`) hit
this: indices 3/19/68 were meant for h09v05, h12v09 and h31v11, but ran other
tiles. Only index 68 (now h12v01) had training labels, and its chips matched
his exactly: same chip, same 521 bands, same labels, and all 163 changed
bands on the v3 fix list.

`full` chips the **63 tiles that were "available" in his 09-09 run**. The
other 6 of his 69 made no chips then (h13v02, h19v07, h20v04, h22v04, h24v02,
h28v11). They're left out so v3 trains on the same tiles as v2, and the only
difference is the metric fixes.

## Running

```bash
cd /explore/nobackup/people/mfrost2/projects/PACE/chips_v3
PY=/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/bin/python

# 1. test: h09v05, h12v09, h31v11
bash launch_chips_v3.sh test
# when done:
$PY compare_chips.py /explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/chip_outputs/metrics_v3/test_<timestamp>

# 2. full run: his 63 tiles that made chips on 09-09
bash launch_chips_v3.sh full
```

A good test result has the same chip ids per tile as his run (19 / 1 / 8), the
same 521 band names in the same order, and identical label chips. Changed
input bands should all be on the v3 fix list; the script flags any that aren't.

## Training (retrain AJ Kerr's chip models on v3)

- `launch_training_v3.sh`: submits one GPU job per model (spatial-cnn,
  pixel-transformer, xgboost) into a new folder under
  `PACE_VCF/models/v3_metrics/chip_models/run_<timestamp>/`.
- `train_model_v3.sbatch`: the per-model job. Settings are copied from his
  2026-09-09 `multi-model-comparison` run: 30 epochs, Huber loss, batch 4,
  same architectures, XAI step, XGBoost with 500 rounds. Only the chips and
  the tile-inference stacks are switched to v3. Pixel-MLP isn't retrained,
  since it isn't one of our four inference models.
- **Split:** random 70/15/15, seed 7, chip by chip, as he did. His code sorts
  chips by ID before shuffling, and the v3 chip IDs are identical, so this
  reproduces his exact split (checked: all 504 chips land in the same split,
  353/76/75).
- **Tile inference during training** uses v3 stacks for h09v05, h12v04,
  h12v09, h20v06 and h31v11. The launcher refuses to submit until they exist.

```bash
cd /explore/nobackup/people/mfrost2/projects/PACE
PY=/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/bin/python
# 1. v3 stacks for the 5 tiles -> PACE_VCF/full_tile_inference_input_v3/
$PY run_multi_model_inference.py prepare-stacks --metrics-version v3 --tiles h09v05 h12v04 h12v09 h20v06 h31v11
# 2. retrain
bash chips_v3/launch_training_v3.sh
```

**Environment:** the training jobs use
`/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python` (set up
2026-10-05). It is a personal venv layered on the ilab jupyter env, adding
`xgboost`, `cupy` and `captum`, which the jupyter env lacks and his trainers
need. The launcher checks these imports before submitting. The chipping
scripts and `run_multi_model_inference.py prepare-stacks` still use the plain
jupyter-env Python, which is all they need.

## After training: XAI, band-count sweep, final models (2026-10-08)

All of these call AJ Kerr's code in place, run as GPU batch jobs, and write
only to new timestamped folders under `PACE_VCF/models/v3_metrics/chip_models/`.

- `eval_chip_models.py`: per-layer R2/RMSE for neural checkpoints on their own
  validation/test chips (his code only logs pooled RMSE). Run it on GPU.
- `launch_xai_v3.sh [run_dir]`: fuller XAI with his standalone tool (all 76
  validation chips, 64 steps, best checkpoint, permutation check) into
  `<model>/XAI_full/`. The XAI inside training (8 chips, 8 steps) is too noisy
  to rank from. The transformer needs `--ig-internal-batch-size 4` on a 32 GB V100.
- `launch_sweep_v3.sh [models]` + `train_sweep_v3.sbatch` +
  `make_topn_lists.py`: retrain each model on its own top 10/25/50/100/200
  tree-cover bands. Bands are selected at training time from the 521-band
  chips (`--exclude-input-band-pattern`), so no new chips are needed. Lean
  jobs: no XAI or tile maps; neural models are scored by a follow-up GPU job.
- `launch_final_v3.sh [models]` + `train_final_v3.sbatch`: the final inference
  models (XGBoost 50, Pixel-Transformer 50, Spatial-CNN 200) with the 5-tile
  maps and automatic scoring. Stops if no GPU is visible. Version-aware
  (2026-10-14): `METRICS_VERSION=v4` = top 100 for all three.
- Multi-seed study (2026-10-14), to measure how stable the band rankings are
  and to pick the v4 finals' bands from the consensus:
  - `launch_seed_study_v3.sh [models]` (all three models, `SEEDS="11 23 37
    41"` default): one independent GPU job per model and seed ->
    `seeds_<timestamp>/`.
  - `train_seed_v3.sbatch`: neural models train on all bands, fuller XAI,
    score, in one job; XGBoost trains only (gain ranking and metrics come
    with it; his XGBoost CLI already has separate `--split-seed`). Same
    settings and same seed-7 chip split as the main training.
  - `train_init_seed.py`: wrapper round his `pace_vcf_toy.train` that keeps
    the split seed (`--seed 7`) but sets the model's random start from
    `--init-seed`. His CLI uses one seed for both.
  - `combine_seed_rankings.py <seeds_dir>`: per-band rank in each seed (the
    existing seed-7 run counts as one), consensus ranking and top 50/100
    lists + patterns, seed-to-seed overlap, accuracy per seed ->
    `<seeds_dir>/combined/`.
  - Then `CONSENSUS_DIR=<seeds_dir>/combined METRICS_VERSION=v4 bash
    launch_final_v3.sh` trains the finals on the consensus top 100.

Runs so far: `run_2026_10_08-09_29_41` (all 521 bands),
`sweep_2026_10_08-11_42_08` and `sweep_2026_10_08-13_15_01` (sweep),
`final_2026_10_08-16_50_47` (final models). Results and insights are in the
main `PACE/README.md`.

## Notes

- His run used an Apptainer container on the ARM `grace` partition. This runs
  his same package with the ilab jupyter-env Python on x86 instead. The
  comparison is what confirms that gives the same chips.
- Each run folder has `tile_index_map.txt` recording which array index went
  to which tile.
