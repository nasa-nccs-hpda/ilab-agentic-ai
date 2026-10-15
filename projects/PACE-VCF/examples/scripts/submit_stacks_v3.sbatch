#!/bin/bash
# Build v3 full-tile input stacks (3-Metrics-v3 -> full_tile_inference_input_v3/)
# for all 291 tiles, lightly: 1 CPU core per task, at most 4 tasks at once,
# no GPU. ~2 min per tile, ~10 CPU-hours in total, ~70-90 GB on disk.
#
# 30 array tasks of 10 tiles each. Each tile runs in its own process so memory
# is released between tiles. Resumable: tiles whose stack already exists are
# skipped, so this is safe to resubmit.
#
#   sbatch submit_stacks_v3.sbatch
#
# To go gentler or faster, change the number after % (max tasks at once):
#   sbatch --array=1-30%2 submit_stacks_v3.sbatch
#SBATCH --job-name=pace-stacks-v3
#SBATCH --array=1-30%4
#SBATCH --cpus-per-task=1
#SBATCH --mem=24G
#SBATCH --time=01:30:00
#SBATCH --output=/explore/nobackup/people/mfrost2/projects/PACE/logs/stacks_v3_%A_%a.out
#SBATCH --error=/explore/nobackup/people/mfrost2/projects/PACE/logs/stacks_v3_%A_%a.err
set -uo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
# Both can be overridden at submit time, e.g. to finish a short list in ONE job:
#   sbatch --array=1 --export=ALL,TILE_LIST=$PWD/tiles_missing_v3_stacks.txt,PER_TASK=50 submit_stacks_v3.sbatch
TILE_LIST="${TILE_LIST:-${PROJECT_DIR}/tiles_all_291.txt}"
PER_TASK="${PER_TASK:-10}"
# Metrics version: v3 (default) or v4 -> full_tile_inference_input_<version>/
#   sbatch --array=1 --export=ALL,METRICS_VERSION=v4,TILE_LIST=$PWD/tiles_check5.txt,PER_TASK=5 submit_stacks_v3.sbatch
METRICS_VERSION="${METRICS_VERSION:-v3}"

# keep every library to the single core this task was given
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 GDAL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
unset GDAL_DATA GDAL_DRIVER_PATH
cd "${PROJECT_DIR}"

FIRST=$(( (SLURM_ARRAY_TASK_ID - 1) * PER_TASK + 1 ))
LAST=$(( SLURM_ARRAY_TASK_ID * PER_TASK ))
mapfile -t TILES < <(sed -n "${FIRST},${LAST}p" "${TILE_LIST}")
echo "metrics ${METRICS_VERSION}"
echo "task ${SLURM_ARRAY_TASK_ID} on $(hostname): ${#TILES[@]} tiles (${TILES[*]})"

FAILED=0
for TILE in "${TILES[@]}"; do
  [[ -n "${TILE}" ]] || continue
  "${PY}" run_multi_model_inference.py prepare-stacks --metrics-version "${METRICS_VERSION}" --tiles "${TILE}" || { echo "FAILED ${TILE}"; FAILED=$((FAILED + 1)); }
done
echo "done: task ${SLURM_ARRAY_TASK_ID}, ${FAILED} failed"
