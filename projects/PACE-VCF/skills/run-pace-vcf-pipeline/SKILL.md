---
name: run-pace-vcf-pipeline
description: "Run, resume, check or extend the PACE-VCF percent-tree-cover pipeline on NASA NCCS Explore (ilab/ADAPT): PACE-OCI metrics -> training chips -> XGBoost / Spatial-CNN / Pixel-Transformer training -> XAI -> band-count sweep -> multi-seed consensus -> final models -> full-tile stacks -> global inference -> comparison with MODIS VCF. Use whenever someone asks to run or check any of these steps, a new metrics version, a MODIS-vs-PACE band test, the comparison notebooks, or what to do next on PACE-VCF, even if they don't name the pipeline. Internal to NCCS; not runnable elsewhere."
---

# PACE-VCF pipeline

Predicts MODIS-VCF percent tree cover (MOD44B) from PACE-OCI metrics with three
models built on a colleague's chip-training code (called in place). This skill says how to run each step, how to
check it, and the house rules that keep shared data and other people's work
safe. The project README is the live record; this skill is the method.

## Before doing anything

1. Read the project README: `/explore/nobackup/people/mfrost2/projects/PACE/README.md`
   -- "Start here", then the status line at the top of the current version's
   plan section (e.g. "v4 plan"), then the last daily-log entry. It names the
   runs, job IDs and decisions that this skill can't know.
2. Find out which metrics version is in play. Every script reads
   `METRICS_VERSION` (`v3` default, `v4` current) through
   `chips_v3/version_config.sh`, which maps it to the chip run, model folder,
   stack folder and band count. Script names keep "_v3" for history; the
   version is the setting, not the file name.

## House rules (and why)

- **Ask the project owner before creating or editing any file**, even small ones, unless they
  just asked for that change; the owner wants to see what changes.
- **The agent cannot submit jobs.** `sbatch` / `squeue` / `sacct` exist only on
  `gpulogin1`, not in the agent's shell or on `adaptlogin201`. Prepare and
  dry-run the launcher, give the owner the exact command, then watch the logs and
  outputs from the filesystem (a background loop that checks once a minute
  and stops on "done:" lines or on Traceback/OOM/CANCELLED/REFUSING).
- **Neural work runs on GPU batch nodes, never on the login node's CPU** --
  training, XAI, scoring and inference for the CNN and transformer. Job
  scripts refuse to start without a GPU; keep that check in new scripts.
- **No multi-task job arrays.** On 2026-10-09 array tasks sharing a node were
  killed when the last task finished. Use a few independent jobs (or a
  one-task array over a tile-list file).
- **Read-only trees:** the colleague's chip-training tree
  `/explore/nobackup/people/ajkerr1/...` (packages imported in place, never
  copied or edited) and the MODIS VCF reference tree
  `/explore/nobackup/people/mcarrol2/...`. Guards in the job scripts refuse
  output under `ajkerr1`.
- **Never overwrite runs or chips.** Every launcher makes a new timestamped
  folder and exits if it exists; keep that pattern in anything new.
- **Light on shared CPU:** 1-core CPU jobs, a handful at a time.
- **Don't touch the shared JupyterHub/ilab env.** Use the project venv.
- Report results faithfully, with the noise level (see "Reading results").

## Environment

```bash
PROJECT=/explore/nobackup/people/mfrost2/projects/PACE
PV=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF          # data root
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python      # GPU torch 2.7.1, xgboost 3.0.5, cupy, captum
```

- xgboost 3.0.5 is the newest that runs on the Tesla V100s (3.1+ fails with
  `cudaErrorNoKernelImageForDevice`). Don't upgrade it.
- Plain JupyterHub env (CPU torch only, no xgboost/captum):
  `/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/bin/python`.
- GDAL/PROJ: GeoTIFF writes can fail with "PROJ: proj_create_from_name". The
  launchers use a private copy of `share/proj` via `PROJ_DATA`/`PROJ_LIB`; in a
  running Python use `osr.SetPROJSearchPaths([copy])`. Always
  `unset GDAL_DATA GDAL_DRIVER_PATH` before running.

## The pipeline

All commands from `$PROJECT` on `gpulogin1`. Times are from the v4 run.

| # | Step | Command | Runs on | Time |
|---|---|---|---|---|
| 1 | Metrics | `bash launch_metrics_v4.sh` (`status` to check) | 4 x 1-core CPU | ~3 h |
| 2 | Chips | `METRICS_VERSION=v4 bash chips_v3/launch_chips_v3.sh full` | 1 CPU job | ~1 h |
| 3 | Check stacks for 5 tiles | `sbatch --array=1 --export=ALL,METRICS_VERSION=v4,TILE_LIST=$PWD/tiles_check5.txt,PER_TASK=5 submit_stacks_v3.sbatch` | CPU | ~10 min |
| 4 | All-band training | `METRICS_VERSION=v4 bash chips_v3/launch_training_v3.sh` | 3 GPU | ~1 h |
| 5 | Fuller XAI | `METRICS_VERSION=v4 bash chips_v3/launch_xai_v3.sh` | 2 GPU | ~30 min |
| 6 | Band-count sweep | `METRICS_VERSION=v4 bash chips_v3/launch_sweep_v3.sh` | 15 GPU + scoring | ~30 min |
| 7 | Multi-seed study | `METRICS_VERSION=v4 bash chips_v3/launch_seed_study_v3.sh` then `$PY chips_v3/combine_seed_rankings.py <seeds_dir>` | 12 GPU; combine is seconds on CPU | ~1 h |
| 8 | Final models | `METRICS_VERSION=v4 CONSENSUS_DIR=<seeds_dir>/combined bash chips_v3/launch_final_v3.sh` | 3 GPU + scoring | ~45 min |
| 9 | All stacks | `bash launch_stacks_v4.sh` | 4 x 1-core CPU | ~1.2 h |
| 10 | Global inference | `MODEL_GROUP=all-v4 bash launch_inference_v3.sh` | 4 GPU | ~1.5 h |
| 11 | Compare maps / features | notebooks 13 and 8b (JupyterHub) | -- | -- |
| side | MODIS-only vs PACE-only | `METRICS_VERSION=v4 bash chips_v3/launch_style_test_v3.sh xgboost spatial-cnn pixel-transformer` | 6 GPU + scoring | ~25 min |
| side | Monte Carlo feature list | notebook `6j_pace_train_chips_v4.ipynb` | JupyterHub | ~5 h |

Per-step commands, checks and decisions: `references/pipeline-steps.md`.

## Reading results

- **Tree cover only** is the target of interest; report other layers only if asked.
- Two R2s exist: chip tables use the coefficient of determination; notebook
  13 uses squared Pearson (the owner's choice). Say which one, never mix them.
- Chip-level split: tiles appear in more than one split, so scores are
  optimistic. Fine for comparing variants, not as an absolute accuracy.
- Noise (v4, all bands, 5 seeds, test RMSE sd): XGBoost +-0.02, CNN +-0.10,
  transformer +-0.07. Fewer bands = noisier neural runs (100-band CNN ranged
  5.77-6.44). Treat single-run differences below that as ties.
- Neural band rankings are unstable between seeds (top-50 shared by two
  seeds: XGBoost 42, CNN 21, transformer 14). Interpret neural importance by
  group (spectral region, season, MODIS vs PACE), not single bands.
- XGBoost importance is gain; neural importance is integrated gradients.
  Compare patterns within a model, not percentages across model types.

## After each step

Update the project README (status line, the version's plan section, daily
log) with run folders, job IDs, results and the owner's decisions. Then give
the owner the next command.
