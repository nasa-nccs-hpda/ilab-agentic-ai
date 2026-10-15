#!/usr/bin/env bash
# Final inference models: each architecture on its own top-N tree-cover bands,
# N chosen from that version's band-count sweep.
#   v3 (MJ, 2026-10-08): xgboost 50, pixel-transformer 50, spatial-cnn 200
#       lists: xgboost, spatial-cnn  sweep_2026_10_08-11_42_08/lists/
#              pixel-transformer     sweep_2026_10_08-13_15_01/lists/
#       (XGBoost was later switched to 200 bands for inference, 2026-10-12)
#   v4 (MJ, 2026-10-14): 100 for all three
#       lists: sweep_2026_10_13-16_42_57/lists/ (seed-7 rankings), or with
#       CONSENSUS_DIR set, the consensus top 100 from the multi-seed study
#       (<seeds_dir>/combined/, made by combine_seed_rankings.py) -- MJ's plan
#       for the v4 finals (2026-10-14).
# The lists are copied into the run folder. Full treatment: 5-tile full-map
# check during training, then a GPU job scores the neural models per layer on
# the val/test chips.
#
# NEVER OVERWRITES: each launch makes a new final_<timestamp> folder.
#
# Usage:
#   bash launch_final_v3.sh                                  # v3, all three
#   METRICS_VERSION=v4 bash launch_final_v3.sh               # v4, all three, seed-7 lists
#   METRICS_VERSION=v4 CONSENSUS_DIR=<seeds_dir>/combined bash launch_final_v3.sh   # v4, consensus lists
#   METRICS_VERSION=v4 bash launch_final_v3.sh spatial-cnn   # a subset
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
BASE="${MODELS_BASE}"
STACKS_V3="${STACKS}"
case "${METRICS_VERSION}" in
  v3)
    declare -A TOPN=([xgboost]=50 [pixel-transformer]=50 [spatial-cnn]=200)
    declare -A LISTS=(
      [xgboost]="${BASE}/sweep_2026_10_08-11_42_08/lists"
      [spatial-cnn]="${BASE}/sweep_2026_10_08-11_42_08/lists"
      [pixel-transformer]="${BASE}/sweep_2026_10_08-13_15_01/lists"
    ) ;;
  v4)
    declare -A TOPN=([xgboost]=100 [pixel-transformer]=100 [spatial-cnn]=100)
    declare -A LISTS=(
      [xgboost]="${BASE}/sweep_2026_10_13-16_42_57/lists"
      [spatial-cnn]="${BASE}/sweep_2026_10_13-16_42_57/lists"
      [pixel-transformer]="${BASE}/sweep_2026_10_13-16_42_57/lists"
    ) ;;
esac
MODELS=("$@"); [[ ${#MODELS[@]} -gt 0 ]] || MODELS=(spatial-cnn pixel-transformer xgboost)

# Source files for one model's list: <prefix>.pattern, <prefix>.txt, and its ranking table.
list_prefix() {  # model n3
  if [[ -n "${CONSENSUS_DIR:-}" ]]; then echo "${CONSENSUS_DIR}/${1}_consensus_top${2}"; else echo "${LISTS[$1]}/${1}_top${2}"; fi
}
ranking_table() {  # model
  if [[ -n "${CONSENSUS_DIR:-}" ]]; then echo "${CONSENSUS_DIR}/${1}_band_stability.csv"; else echo "${LISTS[$1]}/${1}_ranking.csv"; fi
}
if [[ -n "${CONSENSUS_DIR:-}" ]]; then
  [[ -d "${CONSENSUS_DIR}" ]] || { echo "CONSENSUS_DIR ${CONSENSUS_DIR} does not exist" >&2; exit 1; }
  case "$(realpath "${CONSENSUS_DIR}")/" in "$(realpath "${BASE}")"/seeds_*/combined/) ;;
    *) echo "CONSENSUS_DIR must be a <seeds_dir>/combined folder under ${BASE}" >&2; exit 1 ;; esac
fi

for m in "${MODELS[@]}"; do
  [[ -n "${TOPN[$m]:-}" ]] || { echo "unknown model ${m}" >&2; exit 2; }
  n3=$(printf '%03d' "${TOPN[$m]}"); p=$(list_prefix "${m}" "${n3}")
  for f in "${p}.pattern" "${p}.txt" "$(ranking_table "${m}")"; do
    [[ -s "${f}" ]] || { echo "missing ${f}" >&2; exit 1; }
  done
  n_listed=$(grep -c . "${p}.txt")
  [[ "${n_listed}" -eq "${TOPN[$m]}" ]] || { echo "${p}.txt has ${n_listed} bands, expected ${TOPN[$m]}" >&2; exit 1; }
done
for t in h09v05 h12v04 h12v09 h20v06 h31v11; do
  [[ -f "${STACKS_V3}/${t}/input_stack_2km.tif" ]] || { echo "Missing ${METRICS_VERSION} stack for ${t}" >&2; exit 1; }
done

RUN_DIR="${BASE}/final_$(date +%Y_%m_%d-%H_%M_%S)"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs" "${RUN_DIR}/lists"

{
  echo "run_id=$(basename "${RUN_DIR}")"
  echo "kind=final inference models, each on its own top-N tree-cover bands"
  for m in "${MODELS[@]}"; do echo "top_n_${m}=${TOPN[$m]}"; done
  if [[ -n "${CONSENSUS_DIR:-}" ]]; then echo "band_lists=multi-seed consensus: ${CONSENSUS_DIR}"
  else for m in "${MODELS[@]}"; do echo "band_list_${m}=${LISTS[$m]}"; done; fi
  echo "metrics_version=${METRICS_VERSION}"
  echo "chips=${CHIP_RUN}"
  echo "tile_inference_stacks=${STACKS_V3}"
  echo "submitted_by=${USER}"
  echo "submitted_at=$(date -Is)"
} > "${RUN_DIR}/run_metadata.txt"

printf 'model\ttop_n\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
NEURAL_JOBS=(); EVAL_ARGS=()
for m in "${MODELS[@]}"; do
  n3=$(printf '%03d' "${TOPN[$m]}"); p=$(list_prefix "${m}" "${n3}")
  # copied under the usual names, so the run folder looks the same either way
  \cp "${p}.pattern" "${RUN_DIR}/lists/${m}_top${n3}.pattern"
  \cp "${p}.txt" "${RUN_DIR}/lists/${m}_top${n3}.txt"
  \cp "$(ranking_table "${m}")" "${RUN_DIR}/lists/"
  JOB=$(sbatch --parsable --job-name="final-${m}" \
    --output="${RUN_DIR}/slurm_logs/${m}_%j.out" --error="${RUN_DIR}/slurm_logs/${m}_%j.err" \
    --export=ALL,RUN_DIR="${RUN_DIR}",MODEL="${m}",PATTERN_FILE="${RUN_DIR}/lists/${m}_top${n3}.pattern" \
    "${HERE}/train_final_v3.sbatch")
  printf '%s\t%s\t%s\n' "${m}" "${TOPN[$m]}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  echo "Submitted ${m} (top ${TOPN[$m]}): job ${JOB}"
  if [[ "${m}" != xgboost ]]; then NEURAL_JOBS+=("${JOB}"); EVAL_ARGS+=("${m}/top${n3}=${RUN_DIR}/${m}"); fi
done

if [[ ${#NEURAL_JOBS[@]} -gt 0 ]]; then
  DEP="afterany:$(IFS=:; echo "${NEURAL_JOBS[*]}")"
  EJOB=$(sbatch --parsable --job-name="final-eval" --dependency="${DEP}" --gpus=1 --cpus-per-task=4 --mem=64G --time=01:00:00 \
    --output="${RUN_DIR}/slurm_logs/eval_%j.out" --error="${RUN_DIR}/slurm_logs/eval_%j.err" \
    --wrap="unset GDAL_DATA GDAL_DRIVER_PATH; ${PY} -W ignore ${HERE}/eval_chip_models.py --device cuda --out ${RUN_DIR}/final_neural_metrics.csv ${EVAL_ARGS[*]}")
  printf 'eval\t-\t%s\n' "${EJOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  echo "Submitted scoring job ${EJOB} (runs after the neural jobs finish)"
fi
echo "Final run dir: ${RUN_DIR}"
