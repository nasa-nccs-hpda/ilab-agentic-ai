#!/usr/bin/env bash
# Fuller XAI (feature importance) for the v3 neural chip models, using AJ Kerr's
# standalone tool (pace_vcf_toy.xai_cli) in place.
#
# The XAI that runs inside training uses 8 validation chips and 8 integration
# steps on the final-epoch model, which gives noisy rankings. This uses all 76
# validation chips, 64 steps, the best checkpoint (the one used for inference),
# and his permutation check on the top 50 bands.
#
# Writes to <run>/<model>/XAI_full/ ; refuses if that folder exists. The
# training-time <model>/XAI/ folder is not touched.
#
# Usage:
#   bash launch_xai_v3.sh                      # latest run, both neural models
#   bash launch_xai_v3.sh /path/to/run_dir     # a specific training run
set -euo pipefail

source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
BASE="${MODELS_BASE}"
RUN_DIR="${1:-$(ls -td "${BASE}"/run_* | head -1)}"
case "$(realpath "${RUN_DIR}")/" in */ajkerr1/*) echo "REFUSING: run dir under ajkerr1" >&2; exit 1 ;; esac
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
REPO=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf

for MODEL in spatial-cnn pixel-transformer; do
  EXP="${RUN_DIR}/${MODEL}"; OUT="${EXP}/XAI_full"
  [[ -f "${EXP}/run_config.json" ]] || { echo "skip ${MODEL}: no experiment at ${EXP}" >&2; continue; }
  [[ ! -e "${OUT}" ]] || { echo "skip ${MODEL}: ${OUT} already exists" >&2; continue; }
  # Integration steps held on the GPU at once. 16 ran the transformer out of
  # memory on a 32 GB V100 (2026-10-08); 4 is the tool's default.
  IG_BATCH=16; [[ "${MODEL}" == pixel-transformer ]] && IG_BATCH=4
  JOB=$(sbatch --parsable --job-name="xai-${MODEL}" --gpus=1 --cpus-per-task=8 --mem=128G --time=03:00:00 \
    --output="${RUN_DIR}/slurm_logs/xai_${MODEL}_%j.out" --error="${RUN_DIR}/slurm_logs/xai_${MODEL}_%j.err" \
    --wrap="set -euo pipefail; unset GDAL_DATA GDAL_DRIVER_PATH; export PYTHONDONTWRITEBYTECODE=1; cd ${REPO}; \
      PYTHONPATH=toy_model/src ${PY} -m pace_vcf_toy.xai_cli \
        --experiment-dir ${EXP} --output-dir ${OUT} --device cuda \
        --split val --samples 76 --seed 7 \
        --ig-steps 64 --ig-internal-batch-size ${IG_BATCH} \
        --xai-target-bands 0 --top-k 50 \
        --run-permutation --permutation-top-k 50 --permutation-repeats 3; echo done: xai ${MODEL}")
  echo "Submitted XAI for ${MODEL}: job ${JOB} -> ${OUT}"
done
