#!/bin/bash
# Multi-seed study, one job = one model at one model seed, all bands.
# Submit via launch_seed_study_v3.sh (it sets RUN_DIR, MODEL, INIT_SEED).
#
# XGBoost: train only (tree cover; its gain ranking comes with the model).
# Neural models, in one GPU job:
#   1. train (same settings and same seed-7 chip split as train_model_v3.sbatch;
#      only the model's random start differs -- see train_init_seed.py).
#      Lean: no tile maps, no training-time XAI.
#   2. fuller XAI on the best checkpoint (same settings as launch_xai_v3.sh)
#   3. per-layer R2/RMSE on the val/test chips (eval_chip_models.py)
#SBATCH --job-name=pace-seed
#SBATCH --gpus=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --acctg-freq=task=1
set -euo pipefail

PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
AJKERR_REPO=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf
HERE=/explore/nobackup/people/mfrost2/projects/PACE/chips_v3
source "${HERE}/version_config.sh"   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
ALLOWED_BASE="${MODELS_BASE}/"

# --- overwrite guards ---------------------------------------------------------
: "${RUN_DIR:?RUN_DIR not set -- submit with launch_seed_study_v3.sh}"
: "${MODEL:?MODEL not set}"; : "${INIT_SEED:?INIT_SEED not set}"
case "$(realpath -m "${RUN_DIR}")/" in */ajkerr1/*) echo "REFUSING: output under ajkerr1" >&2; exit 1 ;; esac
case "${RUN_DIR}/" in "${ALLOWED_BASE}"seeds_?*) ;; *) echo "REFUSING: output not under ${ALLOWED_BASE}seeds_*" >&2; exit 1 ;; esac
[[ -f "${RUN_DIR}/run_metadata.txt" ]] || { echo "REFUSING: ${RUN_DIR} not created by launch_seed_study_v3.sh" >&2; exit 1; }
mkdir -p "${RUN_DIR}/${MODEL}"
OUT="${RUN_DIR}/${MODEL}/seed_$(printf '%03d' "${INIT_SEED}")"
if ! mkdir "${OUT}"; then echo "REFUSING: ${OUT} already exists" >&2; exit 1; fi

# --- environment ---------------------------------------------------------------
unset GDAL_DATA GDAL_DRIVER_PATH
export PYTHONDONTWRITEBYTECODE=1
cd "${AJKERR_REPO}"   # read-only; his code uses repo-relative paths

# GPU or nothing: stop here rather than ever fall back to CPU.
"${PY}" -c "import torch, sys; ok = torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0) if ok else 'NONE'); sys.exit(0 if ok else 1)" \
  || { echo "REFUSING: no usable GPU on $(hostname)" >&2; exit 1; }

mapfile -t MANIFESTS < <(find "${CHIP_RUN}/raw/manifests/jobs" -name chip_success.jsonl -size +0 | sort)
echo "model=${MODEL} init_seed=${INIT_SEED} manifests=${#MANIFESTS[@]} out=${OUT} node=$(hostname)"

case "${MODEL}" in
  spatial-cnn)
    ARCH_ARGS=(--model spatial-cnn --hidden-channels 64 --residual-blocks 4); IG_BATCH=16 ;;
  pixel-transformer)
    ARCH_ARGS=(--model pixel-transformer --hidden-channels 64 --transformer-attention-heads 4
               --transformer-latents-per-modality 2 --transformer-pixel-chunk-size 32768)
    IG_BATCH=4 ;;  # 16 ran out of memory on a 32 GB V100 (2026-10-08)
  xgboost)
    # His XGBoost CLI already has separate --split-seed and --seed (the seed
    # drives its 80% row / 80% band subsampling per tree). Tree cover only;
    # its ranking is gain from feature_importance.csv, so no XAI step.
    CACHE="${OUT}/xgboost_cache"
    if [[ -d /lscratch && -w /lscratch ]]; then CACHE="/lscratch/${USER}/pace-xgb-${SLURM_JOB_ID}"; fi
    mkdir -p "${CACHE}"
    PYTHONPATH=toy_model/src "${PY}" -m pace_vcf_toy.xgboost_cli \
      --manifest "${MANIFESTS[@]}" --split-mode random --split-seed 7 \
      --train-fraction 0.70 --val-fraction 0.15 --test-fraction 0.15 \
      --output-dir "${OUT}" --cache-dir "${CACHE}" --target-bands 0 \
      --device cuda --nthread "${SLURM_CPUS_PER_TASK:-10}" \
      --n-estimators 500 --early-stopping-rounds 30 --seed "${INIT_SEED}" --plot-samples 4
    rm -rf "${CACHE}"
    printf '{"split_seed": 7, "init_seed": %s}\n' "${INIT_SEED}" > "${OUT}/seeds.json"
    echo "done: ${MODEL} seed ${INIT_SEED}"
    exit 0 ;;
  *) echo "unknown MODEL ${MODEL}" >&2; exit 2 ;;
esac

# 1. train
PYTHONPATH=toy_model/src "${PY}" "${HERE}/train_init_seed.py" --init-seed "${INIT_SEED}" \
  --manifest "${MANIFESTS[@]}" \
  --output-dir "${OUT}" \
  --max-epochs 30 --loss huber \
  --split-mode random --seed 7 --train-fraction 0.70 --val-fraction 0.15 --test-fraction 0.15 \
  --accelerator gpu --devices 1 \
  --batch-size 4 --num-workers 8 --precision 32-true \
  --early-stopping-patience 30 --plot-every-n-epochs 0 \
  "${ARCH_ARGS[@]}"

# 2. fuller XAI (all 76 val chips, 64 steps, best checkpoint, permutation top 50)
PYTHONPATH=toy_model/src "${PY}" -m pace_vcf_toy.xai_cli \
  --experiment-dir "${OUT}" --output-dir "${OUT}/XAI_full" --device cuda \
  --split val --samples 76 --seed 7 \
  --ig-steps 64 --ig-internal-batch-size "${IG_BATCH}" \
  --xai-target-bands 0 --top-k 50 \
  --run-permutation --permutation-top-k 50 --permutation-repeats 3

# 3. scores
"${PY}" -W ignore "${HERE}/eval_chip_models.py" --device cuda --out "${OUT}/chip_metrics.csv" \
  "${MODEL}/seed_${INIT_SEED}=${OUT}"
echo "done: ${MODEL} seed ${INIT_SEED}"
