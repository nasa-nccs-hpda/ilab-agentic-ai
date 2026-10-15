#!/usr/bin/env bash
# Build the v4 full-tile input stacks (3-Metrics-v4 -> full_tile_inference_input_v4/)
# for every tile that does not have one yet, as a few INDEPENDENT 1-core CPU
# jobs (no multi-task job array: array tasks sharing a node were killed on
# 2026-10-09). Each job runs submit_stacks_v3.sbatch as a one-task array over
# its own tile list -- the "one job with TILE_LIST" pattern that worked for the
# missing v3 stacks.
#
# ~1 min and ~0.3 GB per tile (v4 check tiles, 2026-10-13); 286 tiles is about
# 5 CPU-hours and ~90 GB. Resumable: tiles that already have a stack are
# skipped, both here and inside the job.
#
# Usage:
#   bash launch_stacks_v4.sh        # 4 jobs (4 cores at once)
#   bash launch_stacks_v4.sh 2      # gentler
set -euo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
STACKS=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/full_tile_inference_input_v4
NJOBS="${1:-4}"
[[ "${NJOBS}" =~ ^[1-9][0-9]*$ ]] || { echo "number of jobs must be a positive whole number" >&2; exit 2; }

LIST_DIR="${PROJECT_DIR}/logs/stacks_v4_lists_$(date +%Y_%m_%d-%H_%M_%S)"
mkdir -p "${LIST_DIR}"
TODO="${LIST_DIR}/todo.txt"
while read -r t; do
  [[ -n "${t}" ]] || continue
  [[ -s "${STACKS}/${t}/input_stack_2km.tif" ]] || echo "${t}"
done < "${PROJECT_DIR}/tiles_all_291.txt" > "${TODO}"
N=$(grep -c . "${TODO}" || true)
echo "${N} of 291 tiles need a v4 stack"
[[ "${N}" -gt 0 ]] || { echo "Nothing to do."; exit 0; }

PER=$(( (N + NJOBS - 1) / NJOBS ))
split -l "${PER}" -d -a 2 "${TODO}" "${LIST_DIR}/chunk_"
for chunk in "${LIST_DIR}"/chunk_*; do
  n=$(grep -c . "${chunk}")
  JOB=$(sbatch --parsable --array=1 --time=04:00:00 --job-name="stacks-v4" \
    --export=ALL,METRICS_VERSION=v4,TILE_LIST="${chunk}",PER_TASK="${n}" \
    "${PROJECT_DIR}/submit_stacks_v3.sbatch")
  echo "Submitted job ${JOB}: ${n} tiles ($(basename "${chunk}"))"
done
echo "Tile lists: ${LIST_DIR}"
echo "Logs: ${PROJECT_DIR}/logs/stacks_v3_<jobid>_1.out"
