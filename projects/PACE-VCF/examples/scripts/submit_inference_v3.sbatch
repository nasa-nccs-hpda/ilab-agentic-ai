#!/bin/bash
# Tree-cover inference with the three v3 final models, on GPU, for one slice of
# the tile list. Default models (all-v3): XGBoost_v3_top50, Pixel_transformer_v3_top50,
# Spatial_CNN_v3_top200. The final XGBoost (XGBoost_v3_top200) runs with MODEL_GROUP=xgboost_v3_top200.
#
# Submit with launch_inference_v3.sh (it splits the 291 tiles into a few
# INDEPENDENT jobs). This is deliberately NOT a job array: on 2026-10-09 array
# tasks sharing a node were killed, twice, at the moment the array's last task
# finished (see README daily log). Independent jobs have not shown that.
#
# One tile at a time, so a tile the models refuse (e.g. polar tiles with empty
# bands) cannot stop the rest. Resumable: a tile is skipped for a model once its
# output exists. Needs the v3 stacks (full_tile_inference_input_v3/).
#
# Output: PACE_VCF/multi_model_inference/<model>/{tile}_pcttree_2025_{label}.tif
#SBATCH --job-name=pace-infer-v3
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
set -uo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python   # GPU torch + xgboost 3.0.5
TILE_LIST="${TILE_LIST:-${PROJECT_DIR}/tiles_all_291.txt}"
: "${FIRST:?FIRST not set -- submit with launch_inference_v3.sh}"
: "${LAST:?LAST not set}"
# Which models to run: all-v3 (the three final models, default) or any other
# --model value of run_multi_model_inference.py, e.g. xgb-v3-bands.
MODEL_GROUP="${MODEL_GROUP:-all-v3}"

export PYTHONDONTWRITEBYTECODE=1
unset GDAL_DATA GDAL_DRIVER_PATH
cd "${PROJECT_DIR}"

# GPU or nothing: never fall back to CPU for the neural models.
"${PY}" -c "import torch, sys; ok = torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0) if ok else 'NONE'); sys.exit(0 if ok else 1)" \
  || { echo "REFUSING: no usable GPU on $(hostname)" >&2; exit 1; }

mapfile -t TILES < <(sed -n "${FIRST},${LAST}p" "${TILE_LIST}")
echo "models: ${MODEL_GROUP}"
echo "job ${SLURM_JOB_ID} on $(hostname): tiles ${FIRST}-${LAST} of $(basename "${TILE_LIST}") (${#TILES[@]} tiles)"

N=0
for TILE in "${TILES[@]}"; do
  [[ -n "${TILE}" ]] || continue
  N=$((N + 1))
  echo "--- [${N}/${#TILES[@]}] ${TILE} $(date +%H:%M:%S)"
  "${PY}" run_multi_model_inference.py infer --model "${MODEL_GROUP}" --device cuda --tiles "${TILE}" \
    || echo "NONZERO EXIT for ${TILE}"
done
echo "done: tiles ${FIRST}-${LAST}"
