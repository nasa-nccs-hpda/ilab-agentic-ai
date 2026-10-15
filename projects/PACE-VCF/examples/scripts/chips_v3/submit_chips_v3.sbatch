#!/bin/bash
# Chip worker: runs AJ Kerr's chipping CLI for every tile in this run, one
# after another, in ONE job. Submit through launch_chips_v3.sh (it creates
# RUN_DIR and tile_index_map.txt), not directly.
#
# One job, not a job array: on 2026-10-09 array tasks sharing a node were
# killed, twice, when the array's last task finished (README daily log), and a
# chip task was lost the same way on 2026-09-30. ~20-70 s per tile.
#SBATCH --job-name=pace-chips
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --acctg-freq=task=1
set -uo pipefail

PY=/panfs/ccds02/app/modules/jupyter/ilab/jupyter-lab/ilab-juplab-ENV-current/bin/python
AJKERR_REPO=/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/pace_hyperspectral_vcf
HERE=/explore/nobackup/people/mfrost2/projects/PACE/chips_v3
METRICS_VERSION="${METRICS_VERSION:-v3}"   # set by launch_chips_v3.sh
case "${METRICS_VERSION}" in v3|v4) ;; *) echo "REFUSING: METRICS_VERSION must be v3 or v4" >&2; exit 1 ;; esac
ALLOWED_BASE=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/chip_outputs/metrics_${METRICS_VERSION}/

# --- overwrite guards ---------------------------------------------------------
: "${RUN_DIR:?RUN_DIR not set -- submit with launch_chips_v3.sh}"
real_run_dir="$(realpath -m "${RUN_DIR}")"
case "${real_run_dir}/" in
  */ajkerr1/*) echo "REFUSING: output under ajkerr1: ${real_run_dir}" >&2; exit 1 ;;
esac
case "${RUN_DIR}/" in
  "${ALLOWED_BASE}"?*) ;;
  *) echo "REFUSING: output not under ${ALLOWED_BASE}: ${RUN_DIR}" >&2; exit 1 ;;
esac
[[ -f "${RUN_DIR}/run_metadata.txt" ]] || { echo "REFUSING: ${RUN_DIR} not created by launch_chips_v3.sh" >&2; exit 1; }
[[ -s "${RUN_DIR}/tile_index_map.txt" ]] || { echo "REFUSING: no tile_index_map.txt in ${RUN_DIR}" >&2; exit 1; }

# --- environment (see PACE/README.md "Environment gotchas") ------------------
unset GDAL_DATA GDAL_DRIVER_PATH
export PYTHONDONTWRITEBYTECODE=1   # don't try to write __pycache__ into AJ Kerr's src
cd "${AJKERR_REPO}"                # read-only; his CLI uses repo-relative paths

echo "job ${SLURM_JOB_ID:-local} on $(hostname): $(grep -c . "${RUN_DIR}/tile_index_map.txt") tiles, metrics ${METRICS_VERSION}"
N=0; FAILED=0
while read -r INDEX TILE; do
  [[ -n "${INDEX}" ]] || continue
  N=$((N + 1))
  echo "--- [${N}] index ${INDEX} -> ${TILE} $(date +%H:%M:%S)"

  # wrong-tile guard: this index must still point at the tile it was launched for
  if ! "${PY}" "${HERE}/tile_indices.py" check "${INDEX}" "${TILE}"; then
    echo "SKIPPED ${TILE}: tile inventory changed since launch"; FAILED=$((FAILED + 1)); continue
  fi
  # never chip a tile twice into the same run folder
  if [[ -d "${RUN_DIR}/raw/manifests/jobs/tile_${INDEX}" ]]; then
    echo "SKIPPED ${TILE}: already processed in this run"; continue
  fi

  # Identical to his 2026-09-09 python_cli_args, plus --input-metrics-subdir.
  # Wrapped in his run_with_resource_usage.py (as his sbatch does) to record
  # peak memory and exit status -- see slurm_logs/resource_<index>.txt.
  "${PY}" tiling/scripts/run_with_resource_usage.py \
    --output "${RUN_DIR}/slurm_logs/resource_${INDEX}.txt" -- \
    env PYTHONPATH=tiling/src "${PY}" -m pace_hyperspectral.cli \
    --input-base /explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/output \
    --aoi-label-base /explore/nobackup/projects/ilab/data/MODIS/MODIS_VCF/Mark_training/VCF_training_adjusted/tile_adjustment/v5.0.3/geotiff \
    --output-root "${RUN_DIR}/raw" \
    --tile-indices-per-job 1 \
    --job-index "${INDEX}" \
    --job-id "tile_${INDEX}" \
    --input-metrics-subdir "3-Metrics-${METRICS_VERSION}" \
    --label-value-base /css/modis/Collection6/L3/MOD44B-VCF/2020/065 \
    --label-value-filename-template 'MOD44B.A2020065.{tile}.006.*.hdf' \
    --vcf-subdataset-indices 1 2 3 \
    --canonical-crs-source vcf \
    --footprint-relation intersects \
    --edge-policy drop \
    --overlap-fraction 0.0 \
    --label-min-valid-fraction-per-output-pixel 1.0 \
    --exclude-input-band-pattern '^(Unsorted|QA_)' \
    --compression ZSTD \
    --no-progress > "${RUN_DIR}/slurm_logs/tile_${INDEX}_${TILE}.log" 2>&1
  RC=$?
  if [[ "${RC}" -ne 0 ]]; then
    echo "FAILED ${TILE} (exit ${RC}); see slurm_logs/tile_${INDEX}_${TILE}.log"; FAILED=$((FAILED + 1))
  else
    echo "ok ${TILE}: $(ls "${RUN_DIR}/raw/${TILE}/inputs" 2>/dev/null | wc -l) chips"
  fi
done < "${RUN_DIR}/tile_index_map.txt"
echo "done: ${N} tiles, ${FAILED} failed"
