# Sourced by the chips_v3 scripts. Maps a metrics version to its inputs/outputs.
#   METRICS_VERSION=v3 (default) or v4, e.g.  METRICS_VERSION=v4 bash launch_training_v3.sh
# (The scripts keep their "_v3" file names; the version is this setting.)
METRICS_VERSION="${METRICS_VERSION:-v3}"
PACE_VCF=/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF
case "${METRICS_VERSION}" in
  v3) CHIP_RUN="${PACE_VCF}/chip_outputs/metrics_v3/full_2026_09_30-09_59_29"; N_BANDS=521 ;;
  v4) CHIP_RUN="${PACE_VCF}/chip_outputs/metrics_v4/full_2026_10_13-10_17_48"; N_BANDS=475 ;;
  *)  echo "METRICS_VERSION must be v3 or v4, not '${METRICS_VERSION}'" >&2; exit 2 ;;
esac
MODELS_BASE="${PACE_VCF}/models/${METRICS_VERSION}_metrics/chip_models"   # training runs, sweeps, final models
STACKS="${PACE_VCF}/full_tile_inference_input_${METRICS_VERSION}"          # full-tile stacks for this version
export METRICS_VERSION   # so sbatch --export=ALL carries it into the jobs
