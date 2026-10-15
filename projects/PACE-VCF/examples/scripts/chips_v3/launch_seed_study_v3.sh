#!/usr/bin/env bash
# Multi-seed study: how stable are the models' band rankings?
#
# Retrains each model on ALL bands with several model seeds (same seed-7 chip
# split every time, so only the model's random start / subsampling changes).
# Neural models: fuller XAI and scoring on each. XGBoost: its gain ranking and
# metrics come with the model. The existing all-band run (model seed 7) is the
# 5th seed. Afterwards combine with:
#   python combine_seed_rankings.py <seeds_dir>
# and train the final models on the consensus lists:
#   METRICS_VERSION=v4 CONSENSUS_DIR=<seeds_dir>/combined bash launch_final_v3.sh
#
# One independent GPU job per model and seed (no job array). Each launch makes
# a new seeds_<timestamp> folder; never overwrites.
#
# Usage:
#   METRICS_VERSION=v4 bash launch_seed_study_v3.sh                       # all three models, seeds 11 23 37 41
#   METRICS_VERSION=v4 SEEDS="11 23" bash launch_seed_study_v3.sh spatial-cnn
#   REFERENCE_RUN=/path/to/run_dir ...   # seed-7 run to include (default: newest run_*)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
BASE="${MODELS_BASE}"
read -r -a SEEDS <<< "${SEEDS:-11 23 37 41}"
MODELS=("$@"); [[ ${#MODELS[@]} -gt 0 ]] || MODELS=(spatial-cnn pixel-transformer xgboost)
for m in "${MODELS[@]}"; do
  case "${m}" in spatial-cnn|pixel-transformer|xgboost) ;; *) echo "unknown model ${m}" >&2; exit 2 ;; esac
done
for s in "${SEEDS[@]}"; do
  [[ "${s}" =~ ^[0-9]+$ ]] || { echo "seed '${s}' is not a whole number" >&2; exit 2; }
  [[ "${s}" != 7 ]] || { echo "seed 7 is the existing all-band run; leave it out of SEEDS" >&2; exit 2; }
done
if [[ -z "${REFERENCE_RUN:-}" ]]; then
  if [[ "${METRICS_VERSION}" == v3 ]]; then REFERENCE_RUN="${BASE}/run_2026_10_08-09_29_41"
  else REFERENCE_RUN="$(ls -td "${BASE}"/run_* 2>/dev/null | head -1 || true)"; fi
fi
[[ -n "${REFERENCE_RUN}" && -d "${REFERENCE_RUN}" ]] || { echo "No all-band run_* found under ${BASE}; set REFERENCE_RUN=/path" >&2; exit 1; }
for m in "${MODELS[@]}"; do
  if [[ "${m}" == xgboost ]]; then f="${REFERENCE_RUN}/${m}/feature_importance.csv"; else f="${REFERENCE_RUN}/${m}/XAI_full/feature_importance.csv"; fi
  [[ -s "${f}" ]] || echo "WARNING: no ranking for ${m} in ${REFERENCE_RUN}; the study will have one seed fewer" >&2
done

RUN_DIR="${BASE}/seeds_$(date +%Y_%m_%d-%H_%M_%S)"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs"

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=$(basename "${RUN_DIR}")
kind=multi-seed XAI study (all bands; same seed-7 chip split; model seed varies)
models=${MODELS[*]}
init_seeds=${SEEDS[*]}
reference_run_seed7=${REFERENCE_RUN}
metrics_version=${METRICS_VERSION}
chips=${CHIP_RUN}
n_bands=${N_BANDS}
submitted_by=${USER}
submitted_at=$(date -Is)
EOF

printf 'model\tinit_seed\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
for m in "${MODELS[@]}"; do
  for s in "${SEEDS[@]}"; do
    s3=$(printf '%03d' "${s}")
    JOB=$(sbatch --parsable --job-name="seed-${m}-${s}" \
      --output="${RUN_DIR}/slurm_logs/${m}_seed${s3}_%j.out" --error="${RUN_DIR}/slurm_logs/${m}_seed${s3}_%j.err" \
      --export=ALL,RUN_DIR="${RUN_DIR}",MODEL="${m}",INIT_SEED="${s}" \
      "${HERE}/train_seed_v3.sbatch")
    printf '%s\t%s\t%s\n' "${m}" "${s}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  done
  echo "Submitted ${m}: seeds ${SEEDS[*]}"
done
echo "Seed study dir: ${RUN_DIR}"
echo "When all jobs finish: ${HERE}/combine_seed_rankings.py ${RUN_DIR}"
