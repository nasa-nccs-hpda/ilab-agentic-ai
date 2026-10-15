#!/bin/bash
# Metrics v4 for one slice of the tile list (run_metrics_generation_v4.py).
# Submit with launch_metrics_v4.sh, which splits the 291 tiles into a few
# INDEPENDENT jobs (no job arrays on these nodes -- see README 2026-10-09).
#
# CPU only: 1 core, ~2.5 min and ~1.2 GB per tile. One tile per Python process.
# Resumable: a tile whose three v4 files exist with the right band counts is
# skipped, so a job can be resubmitted at any time.
#
# Output: PACE_VCF/output/<tile>/2025/3-Metrics-v4/   (v2 and v3 are not touched)
#SBATCH --job-name=pace-metrics-v4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=06:00:00
set -uo pipefail

PROJECT_DIR=/explore/nobackup/people/mfrost2/projects/PACE
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
TILE_LIST="${TILE_LIST:-${PROJECT_DIR}/tiles_all_291.txt}"
: "${FIRST:?FIRST not set -- submit with launch_metrics_v4.sh}"
: "${LAST:?LAST not set}"

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 GDAL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
unset GDAL_DATA GDAL_DRIVER_PATH
cd "${PROJECT_DIR}"

# The script writes GeoTIFFs with strict GDAL errors on, which needs PROJ's
# database. If PROJ cannot open it in place (seen in a sandboxed shell,
# 2026-10-12), use a private copy.
PROJ_TEST='from osgeo import gdal, osr
gdal.UseExceptions()
s = osr.SpatialReference(); s.ImportFromProj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs")
d = gdal.GetDriverByName("MEM").Create("", 2, 2, 1, gdal.GDT_Int16); d.SetProjection(s.ExportToWkt())
gdal.GetDriverByName("GTiff").CreateCopy("/vsimem/t.tif", d).FlushCache()'
if ! "${PY}" -W ignore -c "${PROJ_TEST}" 2>/dev/null; then
  COPY="${TMPDIR:-/tmp}/pace_proj_${SLURM_JOB_ID:-$$}"
  mkdir -p "${COPY}" && \cp -r /panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/share/proj/. "${COPY}/"
  export PROJ_DATA="${COPY}" PROJ_LIB="${COPY}"
  trap '\rm -rf "${COPY}"' EXIT
  "${PY}" -W ignore -c "${PROJ_TEST}" || { echo "REFUSING: PROJ database unusable even from a copy" >&2; exit 1; }
  echo "PROJ: using private copy at ${COPY}"
fi

mapfile -t TILES < <(sed -n "${FIRST},${LAST}p" "${TILE_LIST}")
echo "job ${SLURM_JOB_ID:-local} on $(hostname): tiles ${FIRST}-${LAST} of $(basename "${TILE_LIST}") (${#TILES[@]} tiles)"

N=0; FAILED=0
for TILE in "${TILES[@]}"; do
  [[ -n "${TILE}" ]] || continue
  N=$((N + 1))
  echo "--- [${N}/${#TILES[@]}] ${TILE} $(date +%H:%M:%S)"
  LOG="$("${PY}" -W ignore run_metrics_generation_v4.py --tile "${TILE}" 2>&1)"; RC=$?
  grep -E "Total:|already complete|Completed" <<< "${LOG}" || true
  if [[ "${RC}" -ne 0 ]]; then
    echo "FAILED ${TILE} (exit ${RC}); last lines:"; tail -n 6 <<< "${LOG}"
    FAILED=$((FAILED + 1))
  fi
done
echo "done: tiles ${FIRST}-${LAST}, ${FAILED} failed"
