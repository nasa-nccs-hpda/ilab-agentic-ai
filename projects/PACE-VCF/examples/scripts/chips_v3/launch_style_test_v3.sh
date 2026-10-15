#!/usr/bin/env bash
# What do the PACE bands add? Retrain on the chips with
#   modis_only : the MODIS-style bands (MODIS_Metrics.tif; MODIS-equivalent
#                bands computed from PACE data, NOT the MODIS sensor)
#   pace_only  : the PACE-style bands  (PACE_Metrics.tif + PACE_AltSort_Metrics.tif)
# and compare tree-cover accuracy with the all-band run.
#   v3: 201 / 320 of 521 bands, reference run_2026_10_08-09_29_41
#   v4: METRICS_VERSION=v4, 195 / 280 of 475 bands, reference run_2026_10_13-13_54_15 Same chips, same seed-7 split, same settings as
# the band-count sweep; bands are selected at training time with
# --exclude-input-band-pattern. Band groups come from each chip band's
# source_modality tag.
#
# Lean jobs (no XAI, no tile maps). XGBoost writes metrics_summary.csv; neural
# models are scored by a follow-up GPU job -> style_neural_metrics.csv.
# Independent jobs, not an array. Each launch makes a new sweep_style_<ts> folder.
#
# Usage:
#   bash launch_style_test_v3.sh                                 # xgboost only
#   bash launch_style_test_v3.sh xgboost spatial-cnn pixel-transformer
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python
source /explore/nobackup/people/mfrost2/projects/PACE/chips_v3/version_config.sh   # METRICS_VERSION -> CHIP_RUN, MODELS_BASE, STACKS, N_BANDS
BASE="${MODELS_BASE}"
CHIP="${CHIP_RUN}/raw/h09v05/inputs/h09v05_r000000_c000000.tif"
MODELS=("$@"); [[ ${#MODELS[@]} -gt 0 ]] || MODELS=(xgboost)
for m in "${MODELS[@]}"; do
  case "${m}" in xgboost|spatial-cnn|pixel-transformer) ;; *) echo "unknown model ${m}" >&2; exit 2 ;; esac
done

RUN_DIR="${BASE}/sweep_style_$(date +%Y_%m_%d-%H_%M_%S)"
if ! mkdir "${RUN_DIR}"; then echo "ERROR: ${RUN_DIR} already exists" >&2; exit 1; fi
mkdir "${RUN_DIR}/slurm_logs" "${RUN_DIR}/lists"

# Band lists and exclude patterns from the chips' own source_modality tags.
unset GDAL_DATA GDAL_DRIVER_PATH
"${PY}" -W ignore - "${CHIP}" "${RUN_DIR}/lists" "${N_BANDS}" <<'EOF'
import re, sys
from pathlib import Path
import rasterio
chip, out = sys.argv[1], Path(sys.argv[2])
with rasterio.open(chip) as s:
    names = [d.strip() for d in s.descriptions]
    mods = [s.tags(i + 1).get("source_modality") for i in range(s.count)]
groups = {"modis_only": [n for n, m in zip(names, mods) if m == "MODIS"],
          "pace_only": [n for n, m in zip(names, mods) if m in ("PACE", "PACE_ALT_SORT")]}
assert len(names) == int(sys.argv[3]) and not set(groups["modis_only"]) & set(groups["pace_only"])
for label, keep_all in groups.items():
    keep = list(dict.fromkeys(keep_all))
    pattern = "^(?!(?:" + "|".join(re.escape(k) for k in keep) + ")$)"
    kept = [n for n in names if not re.search(pattern, n)]
    assert sorted(kept) == sorted(keep_all), label
    (out / f"{label}.txt").write_text("\n".join(keep) + "\n")
    (out / f"{label}.pattern").write_text(pattern)
    print(f"  {label}: {len(kept)} bands")
EOF

cat > "${RUN_DIR}/run_metadata.txt" <<EOF
run_id=$(basename "${RUN_DIR}")
kind=MODIS-style vs PACE-style band test (what do the PACE bands add?)
models=${MODELS[*]}
variants=modis_only ($(grep -c . "${RUN_DIR}/lists/modis_only.txt") bands), pace_only ($(grep -c . "${RUN_DIR}/lists/pace_only.txt") bands); reference = all ${N_BANDS} bands in $(if [[ "${METRICS_VERSION}" == v3 ]]; then echo run_2026_10_08-09_29_41; else echo "run_2026_10_13-13_54_15 (and the 5-seed means in seeds_2026_10_14-09_13_20)"; fi)
metrics_version=${METRICS_VERSION}
chips=${CHIP_RUN}
submitted_by=${USER}
submitted_at=$(date -Is)
EOF

printf 'model\tvariant\tjob_id\n' > "${RUN_DIR}/submitted_jobs.tsv"
NEURAL_JOBS=(); EVAL_ARGS=()
for m in "${MODELS[@]}"; do
  for v in modis_only pace_only; do
    JOB=$(sbatch --parsable --job-name="st-${m}-${v}" \
      --output="${RUN_DIR}/slurm_logs/${m}_${v}_%j.out" --error="${RUN_DIR}/slurm_logs/${m}_${v}_%j.err" \
      --export=ALL,RUN_DIR="${RUN_DIR}",MODEL="${m}",TOPN=0,OUT_NAME="${v}",PATTERN_FILE="${RUN_DIR}/lists/${v}.pattern" \
      "${HERE}/train_sweep_v3.sbatch")
    printf '%s\t%s\t%s\n' "${m}" "${v}" "${JOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
    echo "Submitted ${m} ${v}: job ${JOB}"
    if [[ "${m}" != xgboost ]]; then NEURAL_JOBS+=("${JOB}"); EVAL_ARGS+=("${m}/${v}=${RUN_DIR}/${m}/${v}"); fi
  done
done

if [[ ${#NEURAL_JOBS[@]} -gt 0 ]]; then
  DEP="afterany:$(IFS=:; echo "${NEURAL_JOBS[*]}")"
  EJOB=$(sbatch --parsable --job-name="st-eval" --dependency="${DEP}" --gpus=1 --cpus-per-task=4 --mem=64G --time=01:00:00 \
    --output="${RUN_DIR}/slurm_logs/eval_%j.out" --error="${RUN_DIR}/slurm_logs/eval_%j.err" \
    --wrap="unset GDAL_DATA GDAL_DRIVER_PATH; ${PY} -W ignore ${HERE}/eval_chip_models.py --device cuda --out ${RUN_DIR}/style_neural_metrics.csv ${EVAL_ARGS[*]}")
  printf 'eval\t-\t%s\n' "${EJOB}" >> "${RUN_DIR}/submitted_jobs.tsv"
  echo "Submitted scoring job ${EJOB} (runs after the neural jobs finish)"
fi
echo "Run dir: ${RUN_DIR}"
