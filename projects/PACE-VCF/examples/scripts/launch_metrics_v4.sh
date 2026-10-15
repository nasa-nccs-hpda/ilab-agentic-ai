#!/usr/bin/env bash
# Generate metrics v4 for all tiles as a few INDEPENDENT CPU jobs (not a job
# array). 1 core per job, ~2.5 min per tile: 291 tiles is ~12 CPU-hours,
# about 3 hours with the default 4 jobs.
#
# Usage:
#   bash launch_metrics_v4.sh            # 4 jobs
#   bash launch_metrics_v4.sh 2          # 2 jobs (gentler, ~6 h)
#   TILE_LIST=/path/to/list.txt bash launch_metrics_v4.sh 1   # a short list, one job
#
# Safe to run again: finished tiles are skipped, so a second launch only does
# what is left. Check with:  bash launch_metrics_v4.sh status
set -euo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
TILE_LIST="${TILE_LIST:-${PROJECT_DIR}/tiles_all_291.txt}"
OUT=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/output
TOTAL=$(grep -c . "${TILE_LIST}")

if [[ "${1:-}" == status ]]; then
  DONE=0; MISSING=()
  while read -r t; do
    [[ -n "${t}" ]] || continue
    d="${OUT}/${t}/2025/3-Metrics-v4"
    if [[ -f "${d}/MODIS_Metrics.tif" && -f "${d}/PACE_Metrics.tif" && -f "${d}/PACE_AltSort_Metrics.tif" ]]; then
      DONE=$((DONE + 1)); else MISSING+=("${t}"); fi
  done < "${TILE_LIST}"
  echo "v4 metrics: ${DONE} / ${TOTAL} tiles have all three files"
  [[ ${#MISSING[@]} -eq 0 ]] || echo "missing (${#MISSING[@]}): ${MISSING[*]:0:30}$([[ ${#MISSING[@]} -gt 30 ]] && echo ' ...')"
  exit 0
fi

NJOBS="${1:-4}"
PER=$(( (TOTAL + NJOBS - 1) / NJOBS ))
mkdir -p "${PROJECT_DIR}/logs"
for ((j = 0; j < NJOBS; j++)); do
  FIRST=$(( j * PER + 1 )); LAST=$(( (j + 1) * PER ))
  (( FIRST <= TOTAL )) || break
  (( LAST <= TOTAL )) || LAST=${TOTAL}
  JOB=$(sbatch --parsable --job-name="metrics-v4-$((j + 1))" \
    --output="${PROJECT_DIR}/logs/metrics_v4_%j.out" --error="${PROJECT_DIR}/logs/metrics_v4_%j.err" \
    --export=ALL,FIRST="${FIRST}",LAST="${LAST}",TILE_LIST="${TILE_LIST}" \
    "${PROJECT_DIR}/submit_metrics_v4.sbatch")
  echo "Submitted job ${JOB}: tiles ${FIRST}-${LAST}"
done
echo "Logs: ${PROJECT_DIR}/logs/metrics_v4_<jobid>.out"
echo "Progress: bash ${PROJECT_DIR}/launch_metrics_v4.sh status"
