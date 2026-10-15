#!/usr/bin/env python3
"""
PACE-VCF: percent-tree-cover inference across all MODIS-VCF land tiles.

Models (the `--model` names; output label in quotes)
----------------------------------------------------
Original v2 models (`--model all`), trained on the v2 metrics:
  xgboost_chipped     "XGBoost_100runs"   -- AJ Kerr's chipped XGBoost (external JSON)
  xgboost_tabular     "XGBoost_5000runs"  -- this project's own tabular Monte-Carlo XGBoost
  pixel_transformer   "Pixel_transformer" -- AJ Kerr's Lightning checkpoint
  spatial_cnn         "Spatial_CNN"       -- AJ Kerr's Lightning checkpoint

v3 models, retrained on the v3 metrics chips with AJ Kerr's code, each on its
own top-N tree-cover bands (see chips_v3/README.md and the PACE README):
  xgboost_v3_top200           "XGBoost_v3_top200"            -- FINAL XGBoost (chosen 2026-10-12)
  pixel_transformer_v3_top50  "Pixel_transformer_v3_top50"   -- final Pixel-Transformer
  spatial_cnn_v3_top200       "Spatial_CNN_v3_top200"        -- final Spatial-CNN
  xgboost_v3_top50            "XGBoost_v3_top50"             -- earlier XGBoost choice (0.2 RMSE worse on full tiles)
  xgboost_v3_all521           "XGBoost_v3_all521"            -- all-band reference
Groups: `--model all-v3` = xgboost_v3_top50 + the two final neural models
(the 2026-10-09 global run); `--model xgb-v3-bands` = xgboost_v3_all521 +
xgboost_v3_top200 (the 2026-10-11 band test).

v4 models (added 2026-10-14), retrained on the v4 metrics chips (475 bands, no
duplicates), each on its multi-seed consensus top 100 tree-cover bands; they
read the v4 stacks:
  xgboost_v4_top100           "XGBoost_v4_top100"
  pixel_transformer_v4_top100 "Pixel_transformer_v4_top100"
  spatial_cnn_v4_top100       "Spatial_CNN_v4_top100"  -- model seed 23 (MJ's pick, best on val)
Group: `--model all-v4` = all three.

How it works
------------
Every model except xgboost_tabular runs through AJ Kerr's own
pace_hyperspectral / pace_vcf_toy packages (called in place under
/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/, never copied), over a
pre-built "input_stack_2km.tif" per tile: all 521 metric bands for the whole
tile in his band order, plus the MOD44B labels on the same grid.
  - v2 stacks: full_tile_inference_input/   (prepare-stacks, default)
  - v3 stacks: full_tile_inference_input_v3/ (prepare-stacks --metrics-version v3)
  - v4 stacks: full_tile_inference_input_v4/ (prepare-stacks --metrics-version v4;
    475 bands = everything except Unsorted/QA)
The v3 models read only the v3 stacks and pick their own bands out of the 521
with the same exclude pattern they were trained with.

xgboost_tabular reads features directly from this project's own metrics TIFs,
matching notebooks/7g_inference_C6_xgboost_legacy_subset.ipynb.

Outputs: <PACE_VCF>/multi_model_inference/<model>/{tile}_pcttree_2025_{label}.tif
Existing outputs are skipped, so every command is safe to re-run.

Usage
-----
    # stacks (CPU; in batch use submit_stacks_v3.sbatch)
    $PY run_multi_model_inference.py prepare-stacks --metrics-version v3 --tiles h09v05 h12v04

    # inference (GPU; in batch use launch_inference_v3.sh, which submits
    # independent jobs of submit_inference_v3.sbatch)
    $PY run_multi_model_inference.py infer --model xgboost_v3_top200 --device cuda --tiles h12v09
    $PY run_multi_model_inference.py infer --model all --tiles h12v09 h20v06

Environment
-----------
Use the project's pace-v3 environment by full path (no `conda activate`):

    PY=/explore/nobackup/people/mfrost2/envs/pace-v3/bin/python

It is the ilab jupyter env (Python 3.12, rasterio, lightning) plus a
GPU-enabled torch 2.7.1+cu126, xgboost 3.0.5 (the newest that runs on the
V100 GPUs), cupy and captum. The plain jupyter env still works for
prepare-stacks, but its torch is CPU-only and it has no xgboost.

NOT ilab-pytorch: that env is Python 3.9, and AJ Kerr's pace_vcf_toy uses
`@dataclass(slots=True)`, which needs Python 3.10+ (confirmed 2026-09-28).

Run neural-model inference only as GPU batch jobs, never on a login node.

Things to know about the outputs
--------------------------------
- AJ Kerr's inference fills missing input bands with the tile median, so
  pixels with no PACE data still get a (constant, meaningless) prediction.
  Mask with _raw_chip_predictions/<model>/<tile>/imputed_feature_fraction.tif
  (> 0.5 = essentially no real inputs), as notebook 13 does.
- A tile is refused when one of the model's bands is empty for the whole
  tile: h11v01 and h24v01 for every v3 model (289 of 291 tiles produced).
- Chip-model outputs are unrounded float32 with nodata -255; xgboost_tabular
  is uint8 0-100 with nodata 255.

History: first run end to end 2026-09-28/29 (v2 models, 291 tiles); v3 models
added 2026-10-08, run globally 2026-10-09 and 2026-10-11.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Must happen before rasterio/osgeo are imported (GDAL reads these at driver
# registration time). If this script is launched from a shell with a conda
# env active (e.g. ilab-pytorch), that env's gdal-activate.sh hook has
# already exported GDAL_DATA/GDAL_DRIVER_PATH pointing at ITS OWN gdal
# install -- which then leaks into this completely different Python/GDAL
# build and breaks driver lookup (confirmed 2026-09-28: this exact leak
# caused "plugin gdal_HDF4.so is not available" reading MOD44B .hdf label
# files, even though this env's own rasterio reads that same file fine when
# these vars aren't polluted). Clearing them lets GDAL fall back to the
# defaults baked into this env's own rasterio/gdal packages.
os.environ.pop("GDAL_DATA", None)
os.environ.pop("GDAL_DRIVER_PATH", None)

import numpy as np
import rasterio
import rasterio.transform
import rasterio.crs

# =============================================================================
# CONFIGURATION
# =============================================================================

PACE_BASE = Path("/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/output")
PACE_YEAR = 2025

# AJ Kerr's packages -- reused directly, not copied/reimplemented.
AJKERR_ROOT = Path("/explore/nobackup/people/ajkerr1/PACE_Hyperspectral")
TILING_SRC = AJKERR_ROOT / "pace_hyperspectral_vcf/tiling/src"
TOYMODEL_SRC = AJKERR_ROOT / "pace_hyperspectral_vcf/toy_model/src"
AJKERR_STACK_ROOT = AJKERR_ROOT / "full_tile_outputs_v4"  # 69 tiles, read-only to us

# New tiles' input_stack_2km.tif go here instead of into AJ Kerr's home dir.
OUR_STACK_ROOT = PACE_BASE.parent / "full_tile_inference_input"
# Stacks built from 3-Metrics-v3 (sort/scaling fixes). Kept separate so v2 and
# v3 stacks are never mixed; `prepare-stacks --metrics-version v3` writes here.
V3_STACK_ROOT = PACE_BASE.parent / "full_tile_inference_input_v3"
# Stacks built from 3-Metrics-v4 (no duplicate bands; 475 bands, some renamed).
V4_STACK_ROOT = PACE_BASE.parent / "full_tile_inference_input_v4"
# From v4 on, a stack is simply every band except the Unsorted/QA ones -- the
# same rule AJ Kerr's chipping uses. (v2/v3 stacks instead keep his original
# 521 names, which would silently drop v4's renamed bands.)
TRAINING_BAND_EXCLUSION = r"^(Unsorted|QA_)"

# Exact config used to build AJ Kerr's original 69-tile stacks (from
# full_tile_outputs_v4/run_metadata.txt + prepare_full_tile_inference.py's
# argparse defaults -- only input_base/label_value_base/output_root were
# overridden from default in the original run).
LABEL_VALUE_BASE = Path("/css/modis/Collection6/L3/MOD44B-VCF/2020/065")
LABEL_VALUE_FILENAME_TEMPLATE = "MOD44B.A2020065.{tile}.006.*.hdf"
MODALITIES = ("MODIS", "PACE", "PACE_ALT_SORT")
VCF_SUBDATASET_INDICES = (1, 2, 3)
VCF_SOURCE_NODATA = 255.0
OUTPUT_NODATA = -255.0
VCF_WATER_VALUE = 200.0
LABEL_MIN_VALID_FRACTION = 1.0
LABEL_WATER_FRACTION_THRESHOLD = 0.5
COMPRESSION = "ZSTD"

# AJ Kerr's band_01.json has no embedded feature_names (confirmed 2026-09-28:
# `booster.feature_names is None`), which AJ Kerr's own loader deliberately
# refuses to run with rather than guess the band order. His own
# feature_importance.csv for this same training run records the
# input_band_index -> input_band_name mapping (verified 521/521, no gaps,
# and the order matches the tile stack's own band order at the same
# indices), so it's used to patch a *copy* of the model -- the original
# under ajkerr1's directory is never modified.
AJKERR_XGBOOST_CHIPPED_ORIGINAL = Path(
    "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/"
    "4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-"
    "multi-model-comparison/xgboost/date_2026_09_09-time_14_04_59-"
    "xgboost-37925754/models/band_01.json"
)
AJKERR_XGBOOST_CHIPPED_IMPORTANCE_CSV = (
    AJKERR_XGBOOST_CHIPPED_ORIGINAL.parent.parent / "feature_importance.csv"
)
PATCHED_XGBOOST_CHIPPED_JSON = (
    PACE_BASE.parent / "models" / "ajkerr1_xgboost_chipped_band_01_with_feature_names.json"
)


_ORIGINAL_TRAINING_FEATURE_ORDER: list[str] | None = None


def load_original_training_feature_order() -> list[str]:
    """The exact 521 band names (in training order) AJ Kerr's four models
    were trained on, recovered from his feature_importance.csv. This
    project's own metrics files have grown since his 2026-09-09 run (e.g.
    the Band31/Snow/QA "v2" additions -- confirmed 2026-09-28: preparing a
    stack with no band whitelist now yields 696 bands, not the 521 these
    models expect), so any NEW stack built by this script must be
    restricted to exactly this set, or AJ Kerr's own feature-contract
    checks correctly refuse to run (as they did: "selected=696,
    expected=521"). Cached after first call."""
    global _ORIGINAL_TRAINING_FEATURE_ORDER
    if _ORIGINAL_TRAINING_FEATURE_ORDER is not None:
        return _ORIGINAL_TRAINING_FEATURE_ORDER

    import csv

    rows = [
        r for r in csv.DictReader(open(AJKERR_XGBOOST_CHIPPED_IMPORTANCE_CSV))
        if r["target_band_index"] == "0"  # 0 = Percent_Tree_Cover
    ]
    by_index = {int(r["input_band_index"]): r["input_band_name"] for r in rows}
    if set(by_index) != set(range(len(by_index))):
        raise ValueError(
            "feature_importance.csv input_band_index is not a contiguous 0..N-1 "
            "range -- can't safely reconstruct feature order"
        )
    _ORIGINAL_TRAINING_FEATURE_ORDER = [by_index[i] for i in range(len(by_index))]
    return _ORIGINAL_TRAINING_FEATURE_ORDER


def ensure_patched_xgboost_chipped_model() -> Path:
    """Build (once) a copy of AJ Kerr's band_01.json with feature_names
    attached, recovered from his feature_importance.csv. Idempotent."""
    if PATCHED_XGBOOST_CHIPPED_JSON.exists():
        return PATCHED_XGBOOST_CHIPPED_JSON

    import xgboost as xgb

    feature_names = load_original_training_feature_order()

    booster = xgb.Booster()
    booster.load_model(AJKERR_XGBOOST_CHIPPED_ORIGINAL)
    if booster.num_features() != len(feature_names):
        raise ValueError(
            f"booster has {booster.num_features()} features but recovered "
            f"{len(feature_names)} names -- refusing to patch"
        )
    booster.feature_names = feature_names
    PATCHED_XGBOOST_CHIPPED_JSON.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(PATCHED_XGBOOST_CHIPPED_JSON)
    print(f"  patched xgboost_chipped model written to {PATCHED_XGBOOST_CHIPPED_JSON}")
    return PATCHED_XGBOOST_CHIPPED_JSON


# Four checkpoints, as given.
MODELS = {
    "xgboost_chipped": {
        "label": "XGBoost_100runs",
        "kind": "chip",
        "xgboost_model_json": PATCHED_XGBOOST_CHIPPED_JSON,
        "xgboost_target_band_index": 0,  # 0 = Percent_Tree_Cover
    },
    "pixel_transformer": {
        "label": "Pixel_transformer",
        "kind": "chip",
        "experiment_dir": Path(
            "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/"
            "4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-"
            "multi-model-comparison/pixel-transformer/date_2026_09_09-time_14_04_59-"
            "pixel-transformer-37925753"
        ),
        "checkpoint": Path(
            "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/"
            "4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-"
            "multi-model-comparison/pixel-transformer/date_2026_09_09-time_14_04_59-"
            "pixel-transformer-37925753/checkpoints/epoch=027-val_rmse=8.591.ckpt"
        ),
    },
    "spatial_cnn": {
        "label": "Spatial_CNN",
        "kind": "chip",
        "experiment_dir": Path(
            "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/"
            "4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-"
            "multi-model-comparison/spatial-cnn/date_2026_09_09-time_14_04_59-"
            "spatial-cnn-37925751"
        ),
        "checkpoint": Path(
            "/explore/nobackup/people/ajkerr1/PACE_Hyperspectral/model_outputs/"
            "4_model_comparison/fixed_tiling/date_2026_09_09-time_14_04_58-"
            "multi-model-comparison/spatial-cnn/date_2026_09_09-time_14_04_59-"
            "spatial-cnn-37925751/checkpoints/epoch=026-val_rmse=8.391.ckpt"
        ),
    },
    "xgboost_tabular": {
        "label": "XGBoost_5000runs",
        "kind": "tabular",
        "model_json": Path(
            "/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF/models/"
            "pace_vcf_mc_xgb_20260922_035142.json"
        ),
    },
}

# --- v3 final models (added 2026-10-08) --------------------------------------
# Retrained on the v3 metrics chips, each on its own top-N tree-cover bands
# (N from the 2026-10-08 band-count sweep: XGBoost 50, Pixel-Transformer 50,
# Spatial-CNN 200). They read the v3 stacks (V3_STACK_ROOT, all 521 bands) and
# select their bands with the same exclude pattern used in training. See
# chips_v3/README.md and the PACE README "Insights so far".
FINAL_V3_RUN = (
    PACE_BASE.parent / "models" / "v3_metrics" / "chip_models" / "final_2026_10_08-16_50_47"
)
V3_MODEL_KEYS = ("xgboost_v3_top50", "pixel_transformer_v3_top50", "spatial_cnn_v3_top200")
MODELS.update({
    "xgboost_v3_top50": {
        "label": "XGBoost_v3_top50",
        "kind": "chip",
        "experiment_dir": FINAL_V3_RUN / "xgboost",  # his xgboost experiment (tree cover only)
        "exclude_pattern_file": FINAL_V3_RUN / "lists" / "xgboost_top050.pattern",
        "stack_root": V3_STACK_ROOT,
    },
    "pixel_transformer_v3_top50": {
        "label": "Pixel_transformer_v3_top50",
        "kind": "chip",
        "experiment_dir": FINAL_V3_RUN / "pixel-transformer",
        "checkpoint": FINAL_V3_RUN / "pixel-transformer" / "checkpoints" / "epoch=024-val_rmse=8.442.ckpt",
        "exclude_pattern_file": FINAL_V3_RUN / "lists" / "pixel-transformer_top050.pattern",
        "stack_root": V3_STACK_ROOT,
    },
    "spatial_cnn_v3_top200": {
        "label": "Spatial_CNN_v3_top200",
        "kind": "chip",
        "experiment_dir": FINAL_V3_RUN / "spatial-cnn",
        "checkpoint": FINAL_V3_RUN / "spatial-cnn" / "checkpoints" / "epoch=025-val_rmse=8.514.ckpt",
        "exclude_pattern_file": FINAL_V3_RUN / "lists" / "spatial-cnn_top200.pattern",
        "stack_root": V3_STACK_ROOT,
    },
})
ORIGINAL_MODEL_KEYS = tuple(k for k in MODELS if k not in V3_MODEL_KEYS)

# --- v3 XGBoost band-count test (added 2026-10-11) ----------------------------
# Same v3 chips and split as xgboost_v3_top50, but more bands: all 521, and the
# sweep's top 200. Used to check whether the full-tile gap between the 50-band
# v3 XGBoost and the v2 XGBoost_100runs comes from the band cut.
_V3_CHIP_MODELS = PACE_BASE.parent / "models" / "v3_metrics" / "chip_models"
XGB_V3_BAND_TEST_KEYS = ("xgboost_v3_all521", "xgboost_v3_top200")
MODELS.update({
    "xgboost_v3_all521": {
        "label": "XGBoost_v3_all521",
        "kind": "chip",
        "experiment_dir": _V3_CHIP_MODELS / "run_2026_10_08-09_29_41" / "xgboost",
        "stack_root": V3_STACK_ROOT,  # all 521 stack bands used, no exclude pattern
    },
    "xgboost_v3_top200": {
        "label": "XGBoost_v3_top200",
        "kind": "chip",
        "experiment_dir": _V3_CHIP_MODELS / "sweep_2026_10_08-11_42_08" / "xgboost" / "top200",
        "exclude_pattern_file": _V3_CHIP_MODELS / "sweep_2026_10_08-11_42_08" / "lists" / "xgboost_top200.pattern",
        "stack_root": V3_STACK_ROOT,
    },
})

# --- v4 final models (added 2026-10-14) --------------------------------------
# Retrained on the v4 metrics chips, each on its consensus top 100 tree-cover
# bands from the multi-seed study (seeds_2026_10_14-09_13_20). XGBoost and the
# transformer are the final_2026_10_14-10_10_01 models. The Spatial-CNN is the
# consensus-list model trained at model seed 23 in the CNN check (MJ's choice:
# best of six CNN runs on the validation chips; the seed-7 final was an unlucky
# draw, test RMSE 6.44 vs 5.83). They read the v4 stacks (V4_STACK_ROOT, all
# 475 bands) and select their bands with the pattern used in training.
_V4_CHIP_MODELS = PACE_BASE.parent / "models" / "v4_metrics" / "chip_models"
FINAL_V4_RUN = _V4_CHIP_MODELS / "final_2026_10_14-10_10_01"
CNN_V4_RUN = _V4_CHIP_MODELS / "sweep_cnncheck_2026_10_14-11_33_34"
V4_MODEL_KEYS = ("xgboost_v4_top100", "pixel_transformer_v4_top100", "spatial_cnn_v4_top100")
MODELS.update({
    "xgboost_v4_top100": {
        "label": "XGBoost_v4_top100",
        "kind": "chip",
        "experiment_dir": FINAL_V4_RUN / "xgboost",
        "exclude_pattern_file": FINAL_V4_RUN / "lists" / "xgboost_top100.pattern",
        "stack_root": V4_STACK_ROOT,
    },
    "pixel_transformer_v4_top100": {
        "label": "Pixel_transformer_v4_top100",
        "kind": "chip",
        "experiment_dir": FINAL_V4_RUN / "pixel-transformer",
        "checkpoint": FINAL_V4_RUN / "pixel-transformer" / "checkpoints" / "epoch=029-val_rmse=8.435.ckpt",
        "exclude_pattern_file": FINAL_V4_RUN / "lists" / "pixel-transformer_top100.pattern",
        "stack_root": V4_STACK_ROOT,
    },
    "spatial_cnn_v4_top100": {
        "label": "Spatial_CNN_v4_top100",
        "kind": "chip",
        "experiment_dir": CNN_V4_RUN / "spatial-cnn" / "consensus_seed23",
        "checkpoint": CNN_V4_RUN / "spatial-cnn" / "consensus_seed23" / "checkpoints" / "epoch=022-val_rmse=8.556.ckpt",
        "exclude_pattern_file": CNN_V4_RUN / "lists" / "consensus_top100.pattern",
        "stack_root": V4_STACK_ROOT,
    },
})

# Final output layout: <OUTPUT_BASE>/<model_key>/<tile>_pcttree_<year>_<label>.tif
OUTPUT_BASE = PACE_BASE.parent / "multi_model_inference"

# Raw (pre-extraction) output from AJ Kerr's CLI for the chip models.
CHIP_RAW_OUTPUT_BASE = OUTPUT_BASE / "_raw_chip_predictions"

TILE_SIZE_PACE = 600
MODIS_UPPER_LEFT_X = -20015109.354
MODIS_UPPER_LEFT_Y = 10007554.677
MODIS_TILE_SIZE_M = 1111950.5196666666
NO_DATA_METRICS = -10001  # sentinel used in this project's own metrics TIFs


# =============================================================================
# Shared geospatial helpers (same convention as 7g_inference_C6_xgboost_legacy_subset.ipynb)
# =============================================================================

def get_sinusoidal_crs() -> rasterio.crs.CRS:
    return rasterio.crs.CRS.from_proj4(
        "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs"
    )


def get_transform(tile: str, tile_size: int = TILE_SIZE_PACE):
    h = int(tile[1:3])
    v = int(tile[4:6])
    min_x = MODIS_UPPER_LEFT_X + h * MODIS_TILE_SIZE_M
    max_y = MODIS_UPPER_LEFT_Y - v * MODIS_TILE_SIZE_M
    pixel_size = MODIS_TILE_SIZE_M / tile_size
    return rasterio.transform.from_origin(min_x, max_y, pixel_size, pixel_size)


def final_output_path(model_key: str, tile: str) -> Path:
    label = MODELS[model_key]["label"]
    return OUTPUT_BASE / model_key / f"{tile}_pcttree_{PACE_YEAR}_{label}.tif"


def write_pcttree_geotiff(data: np.ndarray, output_path: Path, tile: str) -> None:
    """Write a single-band Percent_Tree_Cover GeoTIFF, uint8 0-100, nodata=255."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = np.where(
        np.isfinite(data) & (data >= 0) & (data <= 100),
        np.round(data).astype(np.uint8),
        255,
    )
    with rasterio.open(
        output_path, "w",
        driver="GTiff",
        height=out.shape[0], width=out.shape[1],
        count=1, dtype=np.uint8,
        crs=get_sinusoidal_crs(),
        transform=get_transform(tile, out.shape[0]),
        nodata=255,
        compress="lzw", tiled=True,
    ) as dst:
        dst.write(out, 1)
        dst.set_band_description(1, "Percent_Tree_Cover")


# =============================================================================
# Stage: prepare-stacks (only needed for the chip-based models)
# =============================================================================

def discover_all_tiles() -> list[str]:
    """Every tile with completed 3-Metrics output in this project."""
    tiles = []
    for p in sorted(PACE_BASE.iterdir()):
        if p.is_dir() and len(p.name) == 6 and p.name.startswith("h"):
            if (p / str(PACE_YEAR) / "3-Metrics" / "MODIS_Metrics.tif").exists():
                tiles.append(p.name)
    return tiles


STACK_REQUIRED_FILES = ("input_stack_2km.tif", "vcf_labels_2km.tif", "label_valid_mask.tif")


def _stack_complete(root: Path, tile: str) -> bool:
    tile_dir = root / tile
    return all((tile_dir / name).exists() for name in STACK_REQUIRED_FILES)


def resolve_stack_root(tile: str) -> Path | None:
    """Which prepared-stack directory (if any) has a COMPLETE set of files
    for this tile. A tile whose prepare-stacks run failed partway through
    (e.g. input_stack_2km.tif written but vcf_labels_2km.tif never reached)
    must not be treated as ready -- AJ Kerr's own CLI will otherwise reject
    it with a more confusing "tile(s) were not paired" error.

    OUR_STACK_ROOT is checked first, not AJKERR_STACK_ROOT: some of his
    original 69 stacks are stale or outright broken (3 confirmed 2026-09-28
    as 100% NoData across every band -- see knowledge doc), so once a tile
    has been rebuilt into our own directory from current metrics, that
    rebuild must win over his frozen original, not the other way around."""
    if _stack_complete(OUR_STACK_ROOT, tile):
        return OUR_STACK_ROOT
    if _stack_complete(AJKERR_STACK_ROOT, tile):
        return AJKERR_STACK_ROOT
    return None


def compute_new_band_exclusion_pattern(reference_tile: str, metrics_subdir: str = "3-Metrics") -> str:
    """A regex (for ModalityConfig.excluded_band_name_pattern) that excludes
    every band added to this project's metrics files since AJ Kerr's
    2026-09-09 training run, leaving exactly his original 521.

    Can't use an inclusion whitelist (ModalityConfig.selected_band_names)
    instead: two band names in the original 521 -- PACEIndex-REIP-
    Brownest3Mean and PACEIndex-REP-Brownest3Mean -- each legitimately
    occur twice (once in PACE_Metrics.tif, once in PACE_AltSort_Metrics.tif,
    at different stack positions), and selected_band_names rejects
    duplicates outright (confirmed 2026-09-28). Excluding the *new* names
    instead sidesteps this, since none of them collide with that pair --
    verified by rebuilding h23v04 this way and diffing against the original
    521-name list: reproduces it exactly, in order, duplicates included.
    """
    import re

    sys.path.insert(0, str(TILING_SRC))
    from pace_hyperspectral.config import DirectoryStructureConfig, ModalityConfig

    structure = DirectoryStructureConfig(input_year=str(PACE_YEAR), input_metrics_subdir=metrics_subdir)
    unfiltered = ModalityConfig(selected_modalities=MODALITIES)
    current_names: list[str] = []
    for spec in unfiltered.selected_specs:
        path = structure.input_metrics_dir(PACE_BASE, reference_tile) / spec.filename
        with rasterio.open(path) as src:
            current_names.extend(d for d in src.descriptions if d)

    original_set = set(load_original_training_feature_order())
    new_names = [n for n in current_names if n not in original_set]
    return "|".join(f"^{re.escape(n)}$" for n in new_names)


def prepare_stacks(
    tiles: list[str],
    force: bool = False,
    reference_tile: str = "h09v05",
    metrics_subdir: str = "3-Metrics",
    stack_root: Path = OUR_STACK_ROOT,
    exclusion_pattern: str | None = None,
) -> None:
    """Build input_stack_2km.tif for any tile not already prepared by AJ Kerr
    or by a previous run of this script. Reuses his prepare_tile() directly.

    metrics_subdir/stack_root build stacks from another metrics version into
    their own folder, e.g. 3-Metrics-v3 -> V3_STACK_ROOT (added 2026-09-30).
    Stacks from different metrics versions are never mixed in one folder."""
    stack_root = Path(stack_root)
    if "ajkerr1" in stack_root.resolve().parts:
        raise ValueError(f"refusing to write stacks under ajkerr1: {stack_root}")
    if stack_root == OUR_STACK_ROOT and metrics_subdir != "3-Metrics":
        raise ValueError(f"{metrics_subdir} stacks need their own --stack-root, not {OUR_STACK_ROOT}")

    sys.path.insert(0, str(TILING_SRC))
    from pace_hyperspectral.config import DirectoryStructureConfig, ModalityConfig
    from pace_hyperspectral.full_tile import prepare_tile
    from pace_hyperspectral.inventory import TileInventoryRecord

    structure = DirectoryStructureConfig(input_year=str(PACE_YEAR), input_metrics_subdir=metrics_subdir)
    # Restrict to the exact 521 bands AJ Kerr's models were trained on, by
    # excluding everything added since (see compute_new_band_exclusion_pattern).
    # (v4 passes exclusion_pattern=TRAINING_BAND_EXCLUSION instead.)
    by_original_names = exclusion_pattern is None
    if by_original_names:
        exclusion_pattern = compute_new_band_exclusion_pattern(reference_tile, metrics_subdir)
    modality_config = ModalityConfig(
        selected_modalities=MODALITIES,
        excluded_band_name_pattern=exclusion_pattern,
    )
    print(f"  prepare-stacks: {metrics_subdir} -> {stack_root}")
    if by_original_names:
        print(f"  prepare-stacks: excluding {exclusion_pattern.count('|') + 1} bands added since AJ Kerr's training run")
    else:
        print(f"  prepare-stacks: excluding bands matching {exclusion_pattern}")

    if stack_root == OUR_STACK_ROOT:
        todo = tiles if force else [t for t in tiles if resolve_stack_root(t) is None]
    else:
        todo = tiles if force else [t for t in tiles if not _stack_complete(stack_root, t)]
    print(f"prepare-stacks: {len(todo)} / {len(tiles)} tiles need a stack built")

    for index, tile in enumerate(todo):
        input_paths = {
            spec.name: structure.input_metrics_dir(PACE_BASE, tile) / spec.filename
            for spec in modality_config.selected_specs
        }
        missing = tuple(p for p in input_paths.values() if not p.is_file())
        if missing:
            print(f"  SKIP {tile}: missing metrics files {[str(p) for p in missing]}")
            continue

        matches = sorted(
            p for p in LABEL_VALUE_BASE.glob(LABEL_VALUE_FILENAME_TEMPLATE.format(tile=tile))
            if p.is_file()
        )
        if len(matches) != 1:
            print(f"  SKIP {tile}: expected exactly 1 VCF label file, found {len(matches)}")
            continue
        label_path = matches[0]

        record = TileInventoryRecord(
            tile_index=index, tile_id=tile, input_paths=input_paths,
            aoi_label_path=Path(""), label_value_path=label_path,
            discovery_status="available", missing_paths=(),
            missing_input_modalities=(),
            vcf_subdataset_indices=VCF_SUBDATASET_INDICES,
        )
        try:
            result = prepare_tile(
                record, output_root=stack_root,
                modality_config=modality_config,
                vcf_subdataset_indices=VCF_SUBDATASET_INDICES,
                vcf_nodata_value=VCF_SOURCE_NODATA,
                output_nodata_value=OUTPUT_NODATA,
                water_value=VCF_WATER_VALUE,
                label_min_valid_fraction=LABEL_MIN_VALID_FRACTION,
                water_fraction_threshold=LABEL_WATER_FRACTION_THRESHOLD,
                compression=COMPRESSION,
            )
            print(f"  PREPARED {tile} -> {result.input_stack_path}")
        except Exception as exc:  # keep going; report and move to the next tile
            print(f"  FAILED {tile}: {type(exc).__name__}: {exc}")


# =============================================================================
# Stage: chip-based inference (xgboost_chipped / pixel_transformer / spatial_cnn)
# =============================================================================

def run_chip_model(model_key: str, tiles: list[str], device: str = "auto") -> None:
    cfg = MODELS[model_key]
    if model_key == "xgboost_chipped":
        ensure_patched_xgboost_chipped_model()
    raw_output_dir = CHIP_RAW_OUTPUT_BASE / model_key

    by_root: dict[Path, list[str]] = {}
    unresolved = []
    for tile in tiles:
        if "stack_root" in cfg:  # v3 models: only ever read their own stack version
            root = cfg["stack_root"] if _stack_complete(cfg["stack_root"], tile) else None
        else:
            root = resolve_stack_root(tile)
        if root is None:
            unresolved.append(tile)
        else:
            by_root.setdefault(root, []).append(tile)
    if unresolved:
        print(f"  {len(unresolved)} tiles have no prepared stack yet (run prepare-stacks first): "
              f"{unresolved[:10]}{'...' if len(unresolved) > 10 else ''}")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(TOYMODEL_SRC), str(TILING_SRC)] + ([env["PYTHONPATH"]] if "PYTHONPATH" in env else [])
    )

    for stack_root, root_tiles in by_root.items():
        # Skip tiles whose final named output already exists.
        pending = [t for t in root_tiles if not final_output_path(model_key, t).exists()]
        if not pending:
            continue
        print(f"  {model_key}: running {len(pending)} tiles from {stack_root}")

        cmd = [
            sys.executable, "-m", "pace_vcf_toy.full_tile_inference_cli",
            "--tile-inf-input-path", str(stack_root),
            "--tile-inf-label-path", str(stack_root),
            "--tile-inf-tile-ids", *pending,
            "--output-dir", str(raw_output_dir),
            "--device", device,
        ]
        if cfg["kind"] == "chip" and "xgboost_model_json" in cfg:
            cmd += [
                "--xgboost-model-json", str(cfg["xgboost_model_json"]),
                "--xgboost-target-band-index", str(cfg["xgboost_target_band_index"]),
            ]
        else:
            cmd += ["--experiment-dir", str(cfg["experiment_dir"])]
            if "checkpoint" in cfg:
                cmd += ["--checkpoint", str(cfg["checkpoint"])]
        if "exclude_pattern_file" in cfg:
            cmd += ["--tile-inf-exclude-band-pattern", Path(cfg["exclude_pattern_file"]).read_text().strip()]

        result = subprocess.run(cmd, env=env)
        if result.returncode != 0:
            print(f"  WARNING: {model_key} inference exited {result.returncode} "
                  f"for stack root {stack_root} -- check its predictions.tif outputs before trusting them")

        extract_pcttree_from_raw(model_key, pending, raw_output_dir)


def extract_pcttree_from_raw(model_key: str, tiles: list[str], raw_output_dir: Path) -> None:
    """Pull the Percent_Tree_Cover band out of AJ Kerr's predictions.tif and
    write it under our own naming convention, preserving its georeferencing."""
    for tile in tiles:
        src_path = raw_output_dir / tile / "predictions.tif"
        dst_path = final_output_path(model_key, tile)
        if not src_path.exists():
            print(f"    no predictions.tif for {tile} (inference likely failed) -- skipping extraction")
            continue
        with rasterio.open(src_path) as src:
            band_index = next(
                (i + 1 for i, d in enumerate(src.descriptions) if d == "Percent_Tree_Cover"), 1
            )
            data = src.read(band_index)
            profile = src.profile.copy()
            profile.update(count=1, dtype="float32")
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            with rasterio.open(dst_path, "w", **profile) as dst:
                dst.write(data, 1)
                dst.set_band_description(1, "Percent_Tree_Cover")
        print(f"    wrote {dst_path}")


# =============================================================================
# Stage: tabular XGBoost inference (xgboost_tabular) -- no chip stack needed,
# adapted directly from notebooks/7g_inference_C6_xgboost_legacy_subset.ipynb
# =============================================================================

def run_tabular_model(tiles: list[str]) -> None:
    import xgboost as xgb

    cfg = MODELS["xgboost_tabular"]
    model_path = cfg["model_json"]
    timestamp = model_path.stem.replace("pace_vcf_mc_xgb_", "")
    feature_list_path = model_path.parent / f"mc_top_features_{timestamp}.txt"
    if not feature_list_path.exists():
        raise FileNotFoundError(f"No matching feature list for {model_path.name}: expected {feature_list_path}")

    model = xgb.XGBRegressor()
    model.load_model(model_path)
    feature_names = [l.strip() for l in feature_list_path.read_text().splitlines() if l.strip()]
    print(f"  xgboost_tabular: {model_path.name}, {len(feature_names)} features")

    pending = [t for t in tiles if not final_output_path("xgboost_tabular", t).exists()]
    print(f"  {len(pending)} / {len(tiles)} tiles pending")

    for tile in pending:
        metrics_dir = PACE_BASE / tile / str(PACE_YEAR) / "3-Metrics"
        if not metrics_dir.exists():
            print(f"    SKIP {tile}: no metrics at {metrics_dir}")
            continue

        n_pixels = TILE_SIZE_PACE * TILE_SIZE_PACE
        X = np.full((n_pixels, len(feature_names)), np.nan, dtype=np.float32)
        file_data = {}
        for filename in ("MODIS_Metrics.tif", "PACE_Metrics.tif", "PACE_AltSort_Metrics.tif"):
            filepath = metrics_dir / filename
            if filepath.exists():
                with rasterio.open(filepath) as src:
                    band_index = {d: i + 1 for i, d in enumerate(src.descriptions) if d}
                    file_data[filename] = {"path": filepath, "band_index": band_index}

        found = 0
        for i, feat in enumerate(feature_names):
            for fdata in file_data.values():
                if feat in fdata["band_index"]:
                    with rasterio.open(fdata["path"]) as src:
                        data = src.read(fdata["band_index"][feat]).astype(np.float32)
                    data = np.where(data == NO_DATA_METRICS, np.nan, data)
                    data = np.where(data == -255, np.nan, data)
                    X[:, i] = data.flatten()
                    found += 1
                    break
        if found < len(feature_names):
            print(f"    {tile}: only {found}/{len(feature_names)} features found")

        nan_per_pixel = np.sum(np.isnan(X), axis=1)
        valid_mask = (nan_per_pixel < (len(feature_names) * 0.5)).reshape(TILE_SIZE_PACE, TILE_SIZE_PACE)

        y_pred = model.predict(X)
        pred = y_pred.reshape(TILE_SIZE_PACE, TILE_SIZE_PACE)
        pred[~valid_mask] = np.nan
        pred = np.clip(pred, 0, 100)

        write_pcttree_geotiff(pred, final_output_path("xgboost_tabular", tile), tile)
        print(f"    wrote {final_output_path('xgboost_tabular', tile)}")


# =============================================================================
# CLI
# =============================================================================

def load_tiles(args: argparse.Namespace) -> list[str]:
    if args.tiles:
        return list(args.tiles)
    if args.tiles_file:
        return [l.strip() for l in Path(args.tiles_file).read_text().splitlines() if l.strip()]
    return discover_all_tiles()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_tile_args(p):
        p.add_argument("--tiles", nargs="+", help="Explicit tile IDs")
        p.add_argument("--tiles-file", help="File with one tile ID per line")
        p.add_argument("--force", action="store_true")

    p_prepare = sub.add_parser("prepare-stacks", help="Build input_stack_2km.tif for tiles AJ Kerr never processed")
    add_tile_args(p_prepare)
    p_prepare.add_argument("--metrics-version", choices=("v2", "v3", "v4"), default="v2",
                           help="v2 = 3-Metrics -> full_tile_inference_input/ (default); "
                                "v3 = 3-Metrics-v3 -> full_tile_inference_input_v3/; "
                                "v4 = 3-Metrics-v4 -> full_tile_inference_input_v4/ (475 bands)")

    p_infer = sub.add_parser("infer", help="Run inference for one or all models")
    add_tile_args(p_infer)
    p_infer.add_argument(
        "--model", required=True,
        choices=list(MODELS.keys()) + ["all", "all-v3", "xgb-v3-bands", "all-v4"],
        help="'all' = the four original (v2) models; 'all-v3' = the three v3 final models; "
             "'xgb-v3-bands' = v3 XGBoost with all 521 and with 200 bands; "
             "'all-v4' = the three v4 final models",
    )
    p_infer.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")

    args = parser.parse_args()
    tiles = load_tiles(args)
    print(f"{args.command}: {len(tiles)} tiles")

    if args.command == "prepare-stacks":
        if args.metrics_version == "v3":
            prepare_stacks(tiles, force=args.force, metrics_subdir="3-Metrics-v3", stack_root=V3_STACK_ROOT)
        elif args.metrics_version == "v4":
            prepare_stacks(tiles, force=args.force, metrics_subdir="3-Metrics-v4", stack_root=V4_STACK_ROOT,
                           exclusion_pattern=TRAINING_BAND_EXCLUSION)
        else:
            prepare_stacks(tiles, force=args.force)
        return 0

    if args.model == "all":
        model_keys = list(ORIGINAL_MODEL_KEYS)  # unchanged meaning: the four v2 models
    elif args.model == "all-v3":
        model_keys = list(V3_MODEL_KEYS)
    elif args.model == "xgb-v3-bands":
        model_keys = list(XGB_V3_BAND_TEST_KEYS)
    elif args.model == "all-v4":
        model_keys = list(V4_MODEL_KEYS)
    else:
        model_keys = [args.model]
    for model_key in model_keys:
        print(f"=== {model_key} ({MODELS[model_key]['label']}) ===")
        if MODELS[model_key]["kind"] == "chip":
            run_chip_model(model_key, tiles, device=args.device)
        else:
            run_tabular_model(tiles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
