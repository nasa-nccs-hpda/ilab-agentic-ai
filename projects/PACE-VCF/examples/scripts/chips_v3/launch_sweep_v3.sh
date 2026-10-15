#!/usr/bin/env bash
# Band-count sweep: retrain each model on its OWN top 10/25/50/100/200 bands
# (tree-cover ranking) to see where fewer or more bands start to matter.
# The 521-band end point is the full training run itself.
#
# Rankings come from the full training run (see make_topn_lists.py):
#   neural models: <run>/<model>/XAI_full/  (run launch_xai_v3.sh first)
#   xgboost:       tree-cover gain
# Models without a ranking yet are skipped, so this can be run again later for
# them (each launch makes its own new sweep_<timestamp> folder).
#
# After the neural jobs finish, a GPU job scores them per layer on the val/test
# chips -> <sweep>/sweep_neural_metrics.csv. XGBoost writes metrics_summary.csv.
#
# Usage:
#   bash launch_sweep_v3.sh                          # all models that have a ranking
#   bash launch_sweep_v3.sh xgboost spatial-cnn      # a subset
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
BASE="${MODELS_BASE}"
# The all-band training run whose rankings are used: the v3 run of 2026-10-08, or
# for other versions the newest run_* folder. Override with SOURCE_RUN=/path.
if [[ "${METRICS_VERSION}" == v3 ]]; then DEFAULT_SOURCE="${BASE}/run_2026_10_08-09_29_41"
else DEFAULT_SOURCE="$(ls -td "${BASE}"/run_* 2>/dev/null | head -1)"; fi
SOURCE_RUN="${SOURCE_RUN:-${DEFAULT_SOURCE}}"
[[ -d "${SOURCE_RUN}" ]] || { echo "No all-band training run found under ${BASE}" >&2; exit 1; }
NS=(10 25 50 100 200)
MODELS=("$@"); [[ ${#MODELS[@]} -gt 0 ]] || MODELS=(spatial-cnn pixel-transformer xgboost)

RUN_DIR="${BASE}/sweep_$(date +%Y_%m_%d-%H_%M_%S)"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs"

LIST_LOG="$("${PY}" "${HERE}/make_topn_lists.py" "${SOURCE_RUN}" "${RUN_DIR}" --n "${NS[@]}" --n-bands "${N_BANDS}" --models "${MODELS[@]}")"
echo "${LIST_LOG}"
mapfile -t READY < <(sed -n 's/^MODEL //p' <<< "${LIST_LOG}")
if [[ ${#READY[@]} -eq 0 ]]; then echo "No model has a ranking; nothing submitted." >&2; exit 1; fi

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=$(basename "${RUN_DIR}")
kind=band-count sweep (each model on its own top-N tree-cover bands)
models=${READY[*]}
band_counts=${NS[*]}
rankings_from=${SOURCE_RUN}
metrics_version=${METRICS_VERSION}
chips=${CHIP_RUN}
submitted_by=${USER}
submitted_at=$(date -Is)
EOF

printf 'model\ttop_n\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
NEURAL_JOBS=(); EVAL_ARGS=()
for m in "${READY[@]}"; do
  for n in "${NS[@]}"; do
    n3=$(printf '%03d' "${n}")
    JOB=$(sbatch --parsable --job-name="sw-${m}-${n}" \
      --output="${RUN_DIR}/slurm_logs/${m}_top${n3}_%j.out" --error="${RUN_DIR}/slurm_logs/${m}_top${n3}_%j.err" \
      --export=ALL,RUN_DIR="${RUN_DIR}",MODEL="${m}",TOPN="${n}",PATTERN_FILE="${RUN_DIR}/lists/${m}_top${n3}.pattern" \
      "${HERE}/train_sweep_v3.sbatch")
    printf '%s\t%s\t%s\n' "${m}" "${n}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
    if [[ "${m}" != xgboost ]]; then
      NEURAL_JOBS+=("${JOB}"); EVAL_ARGS+=("${m}/top${n3}=${RUN_DIR}/${m}/top${n3}")
    fi
  done
  echo "Submitted ${m}: top ${NS[*]}"
done

if [[ ${#NEURAL_JOBS[@]} -gt 0 ]]; then
  DEP="afterany:$(IFS=:; echo "${NEURAL_JOBS[*]}")"
  EJOB=$(sbatch --parsable --job-name="sw-eval" --dependency="${DEP}" --gpus=1 --cpus-per-task=4 --mem=64G --time=01:00:00 \
    --output="${RUN_DIR}/slurm_logs/eval_%j.out" --error="${RUN_DIR}/slurm_logs/eval_%j.err" \
    --wrap="unset GDAL_DATA GDAL_DRIVER_PATH; ${PY} -W ignore ${HERE}/eval_chip_models.py --device cuda --out ${RUN_DIR}/sweep_neural_metrics.csv ${EVAL_ARGS[*]}")
  printf 'eval\t-\t%s\n' "${EJOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  echo "Submitted scoring job ${EJOB} (runs after the neural jobs finish)"
fi
echo "Sweep dir: ${RUN_DIR}"
