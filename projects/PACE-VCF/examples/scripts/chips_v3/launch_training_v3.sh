#!/usr/bin/env bash
# Retrain AJ Kerr's chip models on the v3 chips, one GPU job per model.
#
# Reproduces his 2026-09-09 multi-model-comparison run
# (ajkerr1/.../model_outputs/4_model_comparison/fixed_tiling/
#  date_2026_09_09-time_14_04_58-multi-model-comparison) with only the chips and
# tile-inference stacks switched to v3. Same seed-7 70/15/15 chip split
# (verified to reproduce his split exactly on the v3 chip IDs).
#
# NEVER OVERWRITES: each launch makes a new timestamped folder under
# PACE_VCF/models/v3_metrics/chip_models/ and exits if it already exists.
#
# Usage:
#   bash launch_training_v3.sh                          # spatial-cnn, pixel-transformer, xgboost
#   bash launch_training_v3.sh spatial-cnn              # any subset
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
OUT_BASE="${MODELS_BASE}"
STACKS_V3="${STACKS}"
MODELS=("$@"); [[ ${#MODELS[@]} -gt 0 ]] || MODELS=(spatial-cnn pixel-transformer xgboost)

# The training jobs run inference on these 5 tiles; they must have v3 stacks.
for t in h09v05 h12v04 h12v09 h20v06 h31v11; do
  for f in input_stack_2km.tif vcf_labels_2km.tif label_valid_mask.tif; do
    [[ -f "${STACKS_V3}/${t}/${f}" ]] || {
      echo "Missing ${METRICS_VERSION} stack ${STACKS_V3}/${t}/${f}. Build the 5 check-tile stacks first (CPU, ~10 min):" >&2
      echo "  cd /explore/nobackup/people/mfrost2/projects/PACE && sbatch --array=1 --export=ALL,METRICS_VERSION=${METRICS_VERSION},TILE_LIST=\$PWD/tiles_check5.txt,PER_TASK=5 submit_stacks_v3.sbatch" >&2
      exit 1; }
  done
done

# Jobs inherit this shell's environment. Check the packages now rather than
# inside the jobs: the neural models import captum (XAI step), XGBoost uses cupy.
NEEDED="torch, lightning"
printf '%s\n' "${MODELS[@]}" | grep -qvx xgboost && NEEDED="${NEEDED}, captum"
printf '%s\n' "${MODELS[@]}" | grep -qx xgboost && NEEDED="${NEEDED}, xgboost, cupy"
"${PY}" -c "import ${NEEDED}" 2>/dev/null || {
  echo "Not importable by ${PY} in this shell: one of ${NEEDED}" >&2
  echo "See chips_v3/README.md (Training: environment)." >&2
  exit 1; }

RUN_ID="run_$(date +%Y_%m_%d-%H_%M_%S)"
RUN_DIR="${OUT_BASE}/${RUN_ID}"
mkdir -p "${OUT_BASE}"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs"

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=${RUN_ID}
models=${MODELS[*]}
submitted_by=${USER}
submitted_at=$(date -Is)
metrics_version=${METRICS_VERSION}
chips=${CHIP_RUN}
tile_inference_stacks=${STACKS_V3}
reproduces=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-multi-model-comparison
differences=${METRICS_VERSION} chips and ${METRICS_VERSION} tile-inference stacks; ilab jupyter env python instead of his arm64 container; pixel-mlp not retrained
EOF

printf 'model\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
for m in "${MODELS[@]}"; do
  JOB=$(sbatch --parsable --job-name="${METRICS_VERSION}-${m}" \
    --output="${RUN_DIR}/slurm_logs/${m}_%j.out" --error="${RUN_DIR}/slurm_logs/${m}_%j.err" \
    --export=ALL,RUN_DIR="${RUN_DIR}",MODEL="${m}" "${HERE}/train_model_v3.sbatch")
  printf '%s\t%s\n' "${m}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  echo "Submitted ${m}: job ${JOB}"
done
echo "Run dir: ${RUN_DIR}  (metrics ${METRICS_VERSION}, ${N_BANDS} bands)"
