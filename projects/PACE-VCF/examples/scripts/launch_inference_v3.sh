#!/usr/bin/env bash
# Submit v3 final-model inference for all tiles as a few INDEPENDENT GPU jobs
# (not a job array -- see submit_inference_v3.sbatch for why).
#
# Usage:
#   bash launch_inference_v3.sh            # 4 jobs = 4 GPUs at once
#   bash launch_inference_v3.sh 2          # 2 jobs (gentler, slower)
#   TILE_LIST=/path/to/list.txt bash launch_inference_v3.sh 1   # a short list, one job
#   MODEL_GROUP=xgb-v3-bands bash launch_inference_v3.sh 2     # other models: v3 XGBoost, 521 and 200 bands
#   MODEL_GROUP=all-v4 bash launch_inference_v3.sh             # the three v4 final models (v4 stacks)
#
# Safe to run again: tiles that already have output are skipped, so a second
# launch only does what is left.
set -euo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
TILE_LIST="${TILE_LIST:-${PROJECT_DIR}/tiles_all_291.txt}"
NJOBS="${1:-4}"
MODEL_GROUP="${MODEL_GROUP:-all-v3}"
# v4 models (MODEL_GROUP=all-v4 or a *_v4_* model) read the v4 stacks
case "${MODEL_GROUP}" in *v4*) SV=v4 ;; *) SV=v3 ;; esac
STACKS=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/full_tile_inference_input_${SV}

TOTAL=$(grep -c . "${TILE_LIST}")
HAVE=$(find "${STACKS}" -name input_stack_2km.tif 2>/dev/null | wc -l)
echo "${TOTAL} tiles in $(basename "${TILE_LIST}"); ${HAVE} ${SV} stacks present"
[[ "${HAVE}" -gt 0 ]] || { echo "No ${SV} stacks found; build them first." >&2; exit 1; }
if [[ "${HAVE}" -lt "${TOTAL}" ]]; then
  echo "NOTE: fewer ${SV} stacks than tiles; tiles without a stack will fail and can be re-run later."
fi

PER=$(( (TOTAL + NJOBS - 1) / NJOBS ))
mkdir -p "${PROJECT_DIR}/logs"
for ((j = 0; j < NJOBS; j++)); do
  FIRST=$(( j * PER + 1 )); LAST=$(( (j + 1) * PER ))
  (( FIRST <= TOTAL )) || break
  (( LAST <= TOTAL )) || LAST=${TOTAL}
  JOB=$(sbatch --parsable --job-name="infer-v3-$((j + 1))" \
    --output="${PROJECT_DIR}/logs/infer_v3_%j.out" --error="${PROJECT_DIR}/logs/infer_v3_%j.err" \
    --export=ALL,FIRST="${FIRST}",LAST="${LAST}",TILE_LIST="${TILE_LIST}",MODEL_GROUP="${MODEL_GROUP}" \
    "${PROJECT_DIR}/submit_inference_v3.sbatch")
  echo "Submitted job ${JOB}: ${MODEL_GROUP}, tiles ${FIRST}-${LAST}"
done
echo "Logs: ${PROJECT_DIR}/logs/infer_v3_<jobid>.out"
