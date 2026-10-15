#!/usr/bin/env bash
# Spatial-CNN band-list check (2026-10-14). The v4 final CNN on the multi-seed
# consensus top 100 scored tree-cover test RMSE 6.44, against 5.77 for the CNN
# on its seed-7 top 100 (sweep) and 5.71 +- 0.10 on all bands. Is that the list
# or one unlucky training run? This trains the CNN on BOTH lists at two more
# model seeds (same seed-7 chip split), so each list has three runs:
#   consensus top 100 : final_2026_10_14-10_10_01 (seed 7) + seeds 11, 23 here
#   seed-7 top 100    : sweep_2026_10_13-16_42_57 (seed 7) + seeds 11, 23 here
# Lean jobs (train_sweep_v3.sbatch: no XAI, no tile maps), then one GPU job
# scores all four -> <run>/cnn_check_metrics.csv. Independent jobs, no array.
# Each launch makes a new sweep_cnncheck_<timestamp> folder; never overwrites.
#
# Usage:  METRICS_VERSION=v4 bash launch_cnn_check_v3.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
[[ "${METRICS_VERSION}" == v4 ]] || { echo "This check is for v4; run with METRICS_VERSION=v4" >&2; exit 2; }
BASE="${MODELS_BASE}"
SEEDS=(11 23)
declare -A LIST_SRC=(
  [consensus]="${BASE}/seeds_2026_10_14-09_13_20/combined/spatial-cnn_consensus_top100"
  [seed7list]="${BASE}/sweep_2026_10_13-16_42_57/lists/spatial-cnn_top100"
)
for v in consensus seed7list; do
  for ext in pattern txt; do [[ -s "${LIST_SRC[$v]}.${ext}" ]] || { echo "missing ${LIST_SRC[$v]}.${ext}" >&2; exit 1; }; done
  [[ "$(grep -c . "${LIST_SRC[$v]}.txt")" -eq 100 ]] || { echo "${LIST_SRC[$v]}.txt is not 100 bands" >&2; exit 1; }
done

RUN_DIR="${BASE}/sweep_cnncheck_$(date +%Y_%m_%d-%H_%M_%S)"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs" "${RUN_DIR}/lists"
for v in consensus seed7list; do
  \cp "${LIST_SRC[$v]}.pattern" "${RUN_DIR}/lists/${v}_top100.pattern"
  \cp "${LIST_SRC[$v]}.txt" "${RUN_DIR}/lists/${v}_top100.txt"
done

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=$(basename "${RUN_DIR}")
kind=Spatial-CNN band-list check: consensus top 100 vs seed-7 top 100, model seeds ${SEEDS[*]} (same seed-7 split)
reference_seed7_consensus=${BASE}/final_2026_10_14-10_10_01/spatial-cnn
reference_seed7_seed7list=${BASE}/sweep_2026_10_13-16_42_57/spatial-cnn/top100
consensus_list=${LIST_SRC[consensus]}.txt
seed7_list=${LIST_SRC[seed7list]}.txt
metrics_version=${METRICS_VERSION}
chips=${CHIP_RUN}
submitted_by=${USER}
submitted_at=$(date -Is)
EOF

printf 'list\tinit_seed\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
JOBS=(); EVAL_ARGS=()
for v in consensus seed7list; do
  for s in "${SEEDS[@]}"; do
    name="${v}_seed${s}"
    JOB=$(sbatch --parsable --job-name="cnnchk-${name}" \
      --output="${RUN_DIR}/slurm_logs/${name}_%j.out" --error="${RUN_DIR}/slurm_logs/${name}_%j.err" \
      --export=ALL,RUN_DIR="${RUN_DIR}",MODEL=spatial-cnn,TOPN=100,OUT_NAME="${name}",INIT_SEED="${s}",PATTERN_FILE="${RUN_DIR}/lists/${v}_top100.pattern" \
      "${HERE}/train_sweep_v3.sbatch")
    printf '%s\t%s\t%s\n' "${v}" "${s}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
    echo "Submitted CNN ${v} seed ${s}: job ${JOB}"
    JOBS+=("${JOB}"); EVAL_ARGS+=("${name}=${RUN_DIR}/spatial-cnn/${name}")
  done
done
# score the two seed-7 reference models too, the same way, in the same file
EVAL_ARGS+=("consensus_seed7=${BASE}/final_2026_10_14-10_10_01/spatial-cnn"
            "seed7list_seed7=${BASE}/sweep_2026_10_13-16_42_57/spatial-cnn/top100")

DEP="afterany:$(IFS=:; echo "${JOBS[*]}")"
EJOB=$(sbatch --parsable --job-name="cnnchk-eval" --dependency="${DEP}" --gpus=1 --cpus-per-task=4 --mem=64G --time=01:00:00 \
  --output="${RUN_DIR}/slurm_logs/eval_%j.out" --error="${RUN_DIR}/slurm_logs/eval_%j.err" \
  --wrap="unset GDAL_DATA GDAL_DRIVER_PATH; ${PY} -W ignore ${HERE}/eval_chip_models.py --device cuda --out ${RUN_DIR}/cnn_check_metrics.csv ${EVAL_ARGS[*]}")
printf 'eval\t-\t%s\n' "${EJOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
echo "Submitted scoring job ${EJOB} (runs after the four training jobs)"
echo "Run dir: ${RUN_DIR}"
