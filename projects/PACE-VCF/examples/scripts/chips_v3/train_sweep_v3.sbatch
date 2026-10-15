#!/bin/bash
# One model trained on a top-N band subset of the v3 chips (band-count sweep).
# Submit via launch_sweep_v3.sh. Same training settings as train_model_v3.sbatch
# (AJ Kerr's 2026-09-09 settings), with two differences:
#   - bands are selected at training time with --exclude-input-band-pattern
#     (pattern read from PATTERN_FILE), from the same 521-band v3 chips;
#   - lean: no XAI, no full-tile inference, no per-epoch plots. Models are
#     scored afterwards on the val/test chips (eval_chip_models.py).
#SBATCH --job-name=pace-sweep-v3
#SBATCH --gpus=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --acctg-freq=task=1
set -euo pipefail

PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
AJKERR_REPO=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
ALLOWED_BASE="${MODELS_BASE}/"

# --- overwrite guards ---------------------------------------------------------
: "${RUN_DIR:?RUN_DIR not set -- submit with launch_sweep_v3.sh}"
: "${MODEL:?MODEL not set}"; : "${TOPN:?TOPN not set}"; : "${PATTERN_FILE:?PATTERN_FILE not set}"
case "$(realpath -m "${RUN_DIR}")/" in */ajkerr1/*) echo "REFUSING: output under ajkerr1" >&2; exit 1 ;; esac
case "${RUN_DIR}/" in "${ALLOWED_BASE}"sweep_?*) ;; *) echo "REFUSING: output not under ${ALLOWED_BASE}sweep_*" >&2; exit 1 ;; esac
[[ -f "${RUN_DIR}/run_metadata.txt" ]] || { echo "REFUSING: ${RUN_DIR} not created by launch_sweep_v3.sh" >&2; exit 1; }
[[ -s "${PATTERN_FILE}" ]] || { echo "REFUSING: empty or missing ${PATTERN_FILE}" >&2; exit 1; }
mkdir -p "${RUN_DIR}/${MODEL}"
# OUT_NAME (optional) names the output folder; default is top<NNN> for the sweep.
# INIT_SEED (optional, neural models): model seed, chip split stays seed 7.
OUT="${RUN_DIR}/${MODEL}/${OUT_NAME:-top$(printf '%03d' "${TOPN}")}"
if ! mkdir "${OUT}"; then echo "REFUSING: ${OUT} already exists" >&2; exit 1; fi

# --- environment ---------------------------------------------------------------
unset GDAL_DATA GDAL_DRIVER_PATH
export PYTHONDONTWRITEBYTECODE=1
cd "${AJKERR_REPO}"   # read-only

PATTERN="$(cat "${PATTERN_FILE}")"
mapfile -t MANIFESTS < <(find "${CHIP_RUN}/raw/manifests/jobs" -name chip_success.jsonl -size +0 | sort)
echo "model=${MODEL} variant=${OUT_NAME:-top${TOPN}} manifests=${#MANIFESTS[@]} out=${OUT} node=$(hostname)"
SPLIT_ARGS=(--train-fraction 0.70 --val-fraction 0.15 --test-fraction 0.15)

case "${MODEL}" in
  spatial-cnn|pixel-transformer)
    if [[ "${MODEL}" == spatial-cnn ]]; then
      ARCH_ARGS=(--model spatial-cnn --hidden-channels 64 --residual-blocks 4)
    else
      ARCH_ARGS=(--model pixel-transformer --hidden-channels 64 --transformer-attention-heads 4
                 --transformer-latents-per-modality 2 --transformer-pixel-chunk-size 32768)
    fi
    # INIT_SEED (optional): different model start, same seed-7 chip split
    # (train_init_seed.py). Unset = his CLI as before.
    ENTRY=(-m pace_vcf_toy.train)
    if [[ -n "${INIT_SEED:-}" ]]; then
      ENTRY=(/explore/nobackup/people/mfrost2/projects/PACE/chips_v3/train_init_seed.py --init-seed "${INIT_SEED}")
    fi
    PYTHONPATH=toy_model/src "${PY}" "${ENTRY[@]}" \
      --manifest "${MANIFESTS[@]}" \
      --output-dir "${OUT}" \
      --exclude-input-band-pattern "${PATTERN}" \
      --max-epochs 30 --loss huber \
      --split-mode random --seed 7 "${SPLIT_ARGS[@]}" \
      --accelerator gpu --devices 1 \
      --batch-size 4 --num-workers 8 --precision 32-true \
      --early-stopping-patience 30 --plot-every-n-epochs 0 \
      "${ARCH_ARGS[@]}"
    ;;
  xgboost)
    CACHE="${OUT}/xgboost_cache"
    if [[ -d /lscratch && -w /lscratch ]]; then CACHE="/lscratch/${USER}/pace-xgb-${SLURM_JOB_ID}"; fi
    mkdir -p "${CACHE}"
    # --target-bands 0: tree cover only (each layer is a separate booster, so
    # the tree model is the same as in a 3-layer run).
    PYTHONPATH=toy_model/src "${PY}" -m pace_vcf_toy.xgboost_cli \
      --manifest "${MANIFESTS[@]}" --split-mode random --split-seed 7 "${SPLIT_ARGS[@]}" \
      --output-dir "${OUT}" --cache-dir "${CACHE}" \
      --exclude-input-band-pattern "${PATTERN}" --target-bands 0 \
      --device cuda --nthread "${SLURM_CPUS_PER_TASK:-10}" \
      --n-estimators 500 --early-stopping-rounds 30 --seed 7 --plot-samples 4 \
      --plot-input-mode single-band --plot-input-band-index 0
    rm -rf "${CACHE}"
    ;;
  *) echo "unknown MODEL ${MODEL}" >&2; exit 2 ;;
esac
echo "done: ${MODEL} ${OUT_NAME:-top${TOPN}}"
