#!/bin/bash
# Final inference model for one architecture: trained on its own top-N
# tree-cover bands (N chosen from the 2026-10-08 band-count sweep), with the
# 5-tile full-map check. Submit via launch_final_v3.sh.
#
# Same settings as train_model_v3.sbatch (AJ Kerr's 2026-09-09 settings).
# Differences: bands selected with --exclude-input-band-pattern (same pattern
# applied to the v3 tile stacks); no in-training XAI (run launch_xai_v3.sh on
# the run folder afterwards for the fuller XAI); XGBoost trains tree cover only.
#SBATCH --job-name=pace-final-v3
#SBATCH --gpus=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --acctg-freq=task=1
set -euo pipefail

PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
AJKERR_REPO=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
ALLOWED_BASE="${MODELS_BASE}/"
STACKS_V3="${STACKS}"
TILE_INF_TILES=(h09v05 h12v04 h12v09 h20v06 h31v11)

# --- overwrite guards ---------------------------------------------------------
: "${RUN_DIR:?RUN_DIR not set -- submit with launch_final_v3.sh}"
: "${MODEL:?MODEL not set}"; : "${PATTERN_FILE:?PATTERN_FILE not set}"
case "$(realpath -m "${RUN_DIR}")/" in */ajkerr1/*) echo "REFUSING: output under ajkerr1" >&2; exit 1 ;; esac
case "${RUN_DIR}/" in "${ALLOWED_BASE}"final_?*) ;; *) echo "REFUSING: output not under ${ALLOWED_BASE}final_*" >&2; exit 1 ;; esac
[[ -f "${RUN_DIR}/run_metadata.txt" ]] || { echo "REFUSING: ${RUN_DIR} not created by launch_final_v3.sh" >&2; exit 1; }
[[ -s "${PATTERN_FILE}" ]] || { echo "REFUSING: empty or missing ${PATTERN_FILE}" >&2; exit 1; }
OUT="${RUN_DIR}/${MODEL}"
if ! mkdir "${OUT}"; then echo "REFUSING: ${OUT} already exists" >&2; exit 1; fi

# --- environment ---------------------------------------------------------------
unset GDAL_DATA GDAL_DRIVER_PATH
export PYTHONDONTWRITEBYTECODE=1
cd "${AJKERR_REPO}"   # read-only

# GPU or nothing: stop here rather than ever fall back to CPU.
"${PY}" -c "import torch, sys; ok = torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0) if ok else 'NONE'); sys.exit(0 if ok else 1)" \
  || { echo "REFUSING: no usable GPU on $(hostname)" >&2; exit 1; }

PATTERN="$(cat "${PATTERN_FILE}")"
mapfile -t MANIFESTS < <(find "${CHIP_RUN}/raw/manifests/jobs" -name chip_success.jsonl -size +0 | sort)
echo "model=${MODEL} pattern=${PATTERN_FILE} manifests=${#MANIFESTS[@]} out=${OUT} node=$(hostname)"

SELECT_ARGS=(--exclude-input-band-pattern "${PATTERN}")
TILE_INF_ARGS=(
  --run-tile-inference --run-tile-inference-every-n-epochs 0
  --tile-inf-input-path "${STACKS_V3}" --tile-inf-label-path "${STACKS_V3}"
  --tile-inf-tile-ids "${TILE_INF_TILES[@]}"
  --tile-inf-exclude-band-pattern "${PATTERN}"
)
PLOT_ARGS=(--plot-input-mode single-band --plot-input-band-index 0)
SPLIT_ARGS=(--train-fraction 0.70 --val-fraction 0.15 --test-fraction 0.15)

case "${MODEL}" in
  spatial-cnn|pixel-transformer)
    if [[ "${MODEL}" == spatial-cnn ]]; then
      ARCH_ARGS=(--model spatial-cnn --hidden-channels 64 --residual-blocks 4)
    else
      ARCH_ARGS=(--model pixel-transformer --hidden-channels 64 --transformer-attention-heads 4
                 --transformer-latents-per-modality 2 --transformer-pixel-chunk-size 32768)
    fi
    PYTHONPATH=toy_model/src "${PY}" -m pace_vcf_toy.train \
      --manifest "${MANIFESTS[@]}" \
      --output-dir "${OUT}" \
      "${SELECT_ARGS[@]}" \
      --max-epochs 30 --loss huber \
      --split-mode random --seed 7 "${SPLIT_ARGS[@]}" \
      --accelerator gpu --devices 1 \
      --batch-size 4 --num-workers 8 --precision 32-true \
      --early-stopping-patience 30 --plot-every-n-epochs 1 \
      "${PLOT_ARGS[@]}" "${TILE_INF_ARGS[@]}" \
      "${ARCH_ARGS[@]}"
    ;;
  xgboost)
    CACHE="${OUT}/xgboost_cache"
    if [[ -d /lscratch && -w /lscratch ]]; then CACHE="/lscratch/${USER}/pace-xgb-${SLURM_JOB_ID}"; fi
    mkdir -p "${CACHE}"
    PYTHONPATH=toy_model/src "${PY}" -m pace_vcf_toy.xgboost_cli \
      --manifest "${MANIFESTS[@]}" --split-mode random --split-seed 7 "${SPLIT_ARGS[@]}" \
      --output-dir "${OUT}" --cache-dir "${CACHE}" \
      "${SELECT_ARGS[@]}" --target-bands 0 \
      --device cuda --nthread "${SLURM_CPUS_PER_TASK:-10}" \
      --n-estimators 500 --early-stopping-rounds 30 --seed 7 --plot-samples 4 \
      "${PLOT_ARGS[@]}" "${TILE_INF_ARGS[@]}"
    rm -rf "${CACHE}"
    ;;
  *) echo "unknown MODEL ${MODEL}" >&2; exit 2 ;;
esac
echo "done: ${MODEL}"
