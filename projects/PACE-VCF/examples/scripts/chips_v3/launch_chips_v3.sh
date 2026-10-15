#!/usr/bin/env bash
# Create v3-metrics training chips with AJ Kerr's chipping code, unchanged.
#
# Reproduces his 2026-09-09 "fixed_metrics" chip run
# (/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/chip_outputs/fixed_metrics/
#  date_2026_09_09-time_13_51_18/run_metadata.txt) with exactly one difference:
# --input-metrics-subdir 3-Metrics-v3.
#
# NEVER OVERWRITES CHIPS: every call makes a brand-new timestamped run
# directory under OUT_BASE and exits if that directory already exists.
# Nothing under ajkerr1/ is written to (the worker also refuses that).
#
# Tiles are given by NAME. His CLI selects a tile by array index into a
# sorted inventory that changes as tiles gain metrics, so indices are looked
# up at launch (tile_indices.py) and each worker re-checks its tile first.
#
# Usage:
#   bash launch_chips_v3.sh test               # h09v05, h12v09, h31v11
#   bash launch_chips_v3.sh full               # his 63 tiles that made chips on 09-09
#   bash launch_chips_v3.sh h20v08 h11v09 ...  # any tiles
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/bin/python
# Metrics version to chip: v3 (default) or v4. Reads 3-Metrics-<version>/ and
# writes under chip_outputs/metrics_<version>/.   METRICS_VERSION=v4 bash launch_chips_v3.sh full
METRICS_VERSION="${METRICS_VERSION:-v3}"
case "${METRICS_VERSION}" in v3|v4) ;; *) echo "METRICS_VERSION must be v3 or v4" >&2; exit 2 ;; esac
OUT_BASE=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/chip_outputs/metrics_${METRICS_VERSION}

case "${1:-}" in
  test) LABEL=test;   TILES=(h09v05 h12v09 h31v11) ;;
  full) LABEL=full;   mapfile -t TILES < <("${PY}" "${HERE}/tile_indices.py" ajkerr-tiles) ;;
  "")   echo "usage: bash $0 {test|full|<tile> ...}" >&2; exit 2 ;;
  *)    LABEL=custom; TILES=("$@") ;;
esac

# tile name -> current inventory index (exits non-zero if a tile isn't in the inventory)
MAP="$(unset GDAL_DATA GDAL_DRIVER_PATH; PYTHONDONTWRITEBYTECODE=1 "${PY}" "${HERE}/tile_indices.py" lookup "${TILES[@]}")"

RUN_ID="${LABEL}_$(date +%Y_%m_%d-%H_%M_%S)"
RUN_DIR="${OUT_BASE}/${RUN_ID}"

mkdir -p "${OUT_BASE}"
# plain mkdir (no -p): fails if the run dir already exists -> never reuse one
if ! mkdir "${RUN_DIR}"; then
  echo "ERROR: ${RUN_DIR} already exists; refusing to write into it." >&2
  exit 1
fi
mkdir "${RUN_DIR}/raw" "${RUN_DIR}/slurm_logs"
printf '%s\n' "${MAP}" > "${RUN_DIR}/tile_index_map.txt"

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=${RUN_ID}
run_dir=${RUN_DIR}
n_tiles=${#TILES[@]}
mode=one job, tiles processed one after another (no job array)
submitted_by=${USER}
submitted_at=$(date -Is)
reproduces=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/chip_outputs/fixed_metrics/date_2026_09_09-time_13_51_18
metrics_version=${METRICS_VERSION}
difference_from_reproduced_run=--input-metrics-subdir 3-Metrics-${METRICS_VERSION} (no container; ilab jupyter env python on x86)
tile_index_map=tile_index_map.txt
EOF

JOB=$(sbatch --parsable \
  --output="${RUN_DIR}/slurm_logs/chips_%j.out" \
  --error="${RUN_DIR}/slurm_logs/chips_%j.err" \
  --export=ALL,RUN_DIR="${RUN_DIR}",METRICS_VERSION="${METRICS_VERSION}" \
  "${HERE}/submit_chips_v3.sbatch")
echo "job_id=${JOB}" >> "${RUN_DIR}/run_metadata.txt"

echo "Submitted job ${JOB}: ${#TILES[@]} tiles, metrics ${METRICS_VERSION}"
echo "Run dir:  ${RUN_DIR}"
echo "Progress: tail -n 3 ${RUN_DIR}/slurm_logs/chips_${JOB}.out"
