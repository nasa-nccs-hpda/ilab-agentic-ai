# PACE-VCF metrics generation, v4 (2026-10-12).
# Writes to 3-Metrics-v4/ ; the v2 (3-Metrics/) and v3 (3-Metrics-v3/) files stay intact.
#
# v4 = v3 with the duplicate bands removed (see README "v4 plan"):
#   1. Amplitude variants now use the sort key, as their names say (they were
#      all the plain max - min): AmpGreenestBandRefl, AmpWarmestBandRefl,
#      PACEIndex-*-AmpGreenness / AmpAnthocyanin / AmpPigmentRatio / AmpStress
#      = value at the highest-key composite minus value at the lowest-key
#      composite (signed; e.g. greenest minus least green).
#   2. Median variants now use the sort key (they were the plain median):
#      BandReflMedianGreenness, BandReflMedianTemp = value at the
#      median-ranked composite of the key.
#   3. Bands that are one quantity under two names are not written
#      (DROPPED_BANDS_V4 below).
#   5. In the PACE file, PACEIndex-<Index>-Greenest3Mean is renamed
#      PACEIndex-<Index>-Highest3Mean: it is the mean of the index's own 3
#      highest values, not the index at the 3 greenest composites.
#   4. PACEIndex-REP/REIP-Brownest3Mean existed twice under one name; the
#      PACE-file copy (lowest 3 values of the index itself) is renamed
#      PACEIndex-REP/REIP-Lowest3Mean. The AltSort copy (index at the 3
#      lowest-NDVI composites) keeps the name, like the other ten indices.
# Reference for intent: nasa-nccs-hpda/modis_vcf, branch mcarrol2/v1.2.0,
# model/Metrics.py (commit 7036b6a).
# v3 (2026-09-29): fixes the key-sorted metric bugs -- see mean_at_extreme().
# Writes to 3-Metrics-v3/ so the v2 files used by existing models stay intact.
#!/usr/bin/env python
# coding: utf-8

# In[1]:


# =============================================================================
# Notebook 3: PACE-VCF Metrics Calculation (UPDATED v2)
# =============================================================================
# Purpose: Calculate VCF metrics from PACE composites
#
# UPDATES in v2:
#   - Added Band31 (thermal) basic metrics
#   - Added snow detection and snow-free metrics
#   - Added QA observation count metrics (diagnostic only, prefix QA_)
#   - Improved thermal-sorted metrics for all bands including Band31
#
# Output Format: MODIS-compatible Int16 with scaling
#   - Reflectance: × 10,000
#   - NDVI and indices: × 1,000
#   - Thermal: × 100 (Kelvin)
#   - No-data: -10001
#
# Input:
#   - wavelengths/*.bin (84 wavelengths × 12 composites)
#   - aggregated/*.bin (7 bands × 12 composites)
#   - thermal/*.bin (Band31 × 12 composites)
#
# Output:
#   - MODIS_Metrics.tif (~290 bands, Int16) - increased with Band31 & snow
#   - PACE_Metrics.tif (~146 bands, Int16)
#   - PACE_AltSort_Metrics.tif (~250 bands, Int16)
#
# Author: MJ Frost
# Date: August 2026
# =============================================================================


# %% Cell 1: Configuration
from pathlib import Path
import numpy as np

import os

# Set default file permissions to 022 (creates files with 755 for dirs, 644 for files)
os.umask(0o022)

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path("/explore/nobackup/projects/ilab/data/MODIS/PACE_VCF")
OUTPUT_BASE = DATA_DIR / "output"
METRICS_SUBDIR = "3-Metrics-v4"
# Where the metrics are written. Defaults to the project output tree; set the
# environment variable PACE_METRICS_OUT_BASE to write somewhere else (used for
# the v3-vs-v4 regression so test output never lands in the real folder).
import os as _os
METRICS_OUT_BASE = Path(_os.environ.get("PACE_METRICS_OUT_BASE", str(OUTPUT_BASE)))

TILES_TO_PROCESS = [
    "h08v04", "h08v05", "h09v04", "h09v05", "h10v04", "h10v05", "h10v06",
    "h11v02", "h11v03", "h11v04", "h11v05", "h11v08", "h11v09", "h11v10",
    "h12v01", "h12v02", "h12v03", "h12v04", "h12v05", "h12v09", "h12v10", 
    "h12v12", "h13v01", "h13v02", "h13v10", "h13v11", "h13v12", "h16v01", 
    "h17v05", "h18v03", "h18v04", "h18v07", "h19v04", "h19v07", "h19v08", 
    "h19v09", "h19v10", "h19v11", "h19v12", "h20v02", "h20v03", "h20v04", 
    "h20v06", "h20v08", "h20v09", "h20v10", "h20v11", "h21v01", "h21v02",
    "h21v04", "h21v05", "h21v06", "h21v10", "h22v03", "h22v04", "h23v02", 
    "h23v03", "h24v02", "h24v03", "h24v04", "h26v06", "h27v04", "h27v06", 
    "h27v07", "h28v11", "h29v11", "h29v12", "h30v12", "h31v11"
]
YEAR = 2025

TILE_SIZE = 600
NO_DATA_INT = -10001
SCALE_FACTOR_INPUT = 10000

REFL_SCALE = 10000
NDVI_SCALE = 1000
INDEX_SCALE = 1000
THERMAL_SCALE = 100

COMPOSITE_DOYS = [
    '2025065', '2025097', '2025129', '2025161',
    '2025193', '2025225', '2025257', '2025289',
    '2025321', '2025353', '2026020', '2026052'
]

BANDS = ['Band_1', 'Band_2', 'Band_3', 'Band_4', 'Band_5', 'Band_6', 'Band_7']
BAND_THERMAL = 'Band31'

# All bands including thermal for some metrics
ALL_BANDS = BANDS + [BAND_THERMAL]

WAVELENGTHS = [
    450, 455, 460, 465, 470, 475, 480,
    505, 510, 515, 520, 525, 530, 535, 540,
    545, 550, 555, 560, 565, 570, 575, 580, 586,
    615, 620, 625, 630, 635, 640, 642, 645, 647, 650, 652,
    655, 657, 660, 662, 665, 667, 670, 672, 675, 677, 679, 682,
    697, 699, 702, 704, 707, 709, 712, 714, 719, 724, 729, 734, 739, 742, 744, 747, 749, 752, 754,
    835, 840, 845, 850, 855, 860, 865, 870, 875, 880, 885, 890, 895,
    1038, 1249, 1618, 2131, 2258
]

print("Configuration loaded")
print(f"  Tiles: {TILES_TO_PROCESS}")
print(f"  Composites: {len(COMPOSITE_DOYS)}")
print(f"  Output format: Int16")
print(f"  NEW: Band31 thermal metrics")
print(f"  NEW: Snow detection metrics")
print(f"  NEW: QA observation count metrics")


# %% Cell 2: Imports
import logging
from typing import Dict, List, Tuple, Optional
from osgeo import gdal, osr
import warnings
warnings.filterwarnings('ignore')

gdal.UseExceptions()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("Imports complete")


# %% Cell 3: Scaling Functions
# =============================================================================
# Scale factors for Int16 output (MODIS-compatible)
# =============================================================================

NO_DATA = -10001

def scale_reflectance(data: np.ndarray) -> np.ndarray:
    """Scale reflectance (0-1) to Int16 (0-10000). MODIS convention: × 10,000"""
    with np.errstate(all='ignore'):
        scaled = data * 10000
        scaled = np.where(np.isfinite(scaled), scaled, NO_DATA)
    return scaled.astype(np.int16)


def scale_ndvi(data: np.ndarray) -> np.ndarray:
    """Scale NDVI (-1 to 1) to Int16 (-1000 to 1000). MODIS convention: × 1,000"""
    with np.errstate(all='ignore'):
        scaled = data * 1000
        scaled = np.where(np.isfinite(scaled), scaled, NO_DATA)
    return scaled.astype(np.int16)


def scale_index(data: np.ndarray) -> np.ndarray:
    """Scale vegetation index to Int16. Convention: × 1,000"""
    with np.errstate(all='ignore'):
        scaled = data * 1000
        scaled = np.clip(scaled, -32767, 32767)
        scaled = np.where(np.isfinite(scaled), scaled, NO_DATA)
    return scaled.astype(np.int16)


def scale_thermal(data: np.ndarray) -> np.ndarray:
    """
    Scale temperature (Kelvin) to Int16. MODIS convention: × 100
    Note: Temps > 327.67 K are clamped to 32767 to prevent overflow.
    Only for absolute temperatures (expects 200-400 K range) -- for
    amplitudes/ranges/differences (which will never fall in that range),
    use scale_thermal_diff() instead. AmpBandRefl-Band31 and
    ThermalGreenBrownDiff-Band31 were silently 0% valid tile-wide for a
    long stretch of the notebook history because they were run through
    this function instead: every value failed the > 200 and < 400 gate
    since a temperature *difference* is never actually in that range.
    """
    result = np.full(data.shape, NO_DATA, dtype=np.int16)
    valid = np.isfinite(data) & (data > 200) & (data < 400)

    if np.any(valid):
        scaled = data[valid].astype(np.float64) * 100
        scaled = np.clip(scaled, -32767, 32767)
        result[valid] = scaled.astype(np.int16)

    return result


def scale_thermal_diff(data: np.ndarray) -> np.ndarray:
    """
    Scale temperature DIFFERENCE to Int16. MODIS convention: × 100
    For amplitudes, ranges, and differences (no absolute temp constraint) --
    see scale_thermal()'s docstring for why this is a separate function.
    """
    result = np.full(data.shape, NO_DATA, dtype=np.int16)
    valid = np.isfinite(data)

    if np.any(valid):
        scaled = data[valid].astype(np.float64) * 100
        scaled = np.clip(scaled, -32767, 32767)
        result[valid] = scaled.astype(np.int16)

    return result


def scale_rep(arr: np.ndarray, no_data: int = -10001) -> np.ndarray:
    """Scale REP/REIP from nm to Int16. 705.5 nm -> 7055 (× 10)"""
    scaled = arr * 10
    scaled = np.where(np.isfinite(scaled), scaled, no_data)
    return np.clip(scaled, -32767, 32767).astype(np.int16)


def scale_idx_named(idx_name: str, data: np.ndarray) -> np.ndarray:
    """v3: REP/REIP are wavelengths (nm), not unitless indices -- scale x10 like
    PACE_Metrics.tif does. v2 used scale_index (x1000, clipped at 32767), which
    saturated 26 of 36 REP/REIP bands in PACE_AltSort_Metrics.tif."""
    return scale_rep(data) if idx_name in ("REP", "REIP") else scale_index(data)


print("Scaling functions defined (MODIS-compatible)")
print(f"  Reflectance: × {REFL_SCALE}")
print(f"  NDVI/Index:  × {NDVI_SCALE}")
print(f"  Temperature: × {THERMAL_SCALE} (clamped to ±32767)")


# %% Cell 4: NDVI Functions
def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Calculate NDVI from Red (Band_1) and NIR (Band_2)."""
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir - red) / (nir + red)
        ndvi = np.clip(ndvi, -1, 1)
        ndvi = np.where(np.isfinite(ndvi), ndvi, np.nan)
    return ndvi


def get_ndvi_cube(bands: dict) -> np.ndarray:
    """Calculate NDVI cube from bands dictionary."""
    return calculate_ndvi(bands['Band_1'], bands['Band_2'])


print("NDVI functions defined")


# %% Cell 5: Data Loading Functions
def load_band_cube(composite_dir: Path, tile: str, band_name: str) -> Tuple[np.ndarray, List[str]]:
    """
    Load all composites for a single band into a 3D cube.
    Returns data as FLOAT for calculations (scaled on output).
    """
    cube = []
    doy_list = []

    if band_name == BAND_THERMAL:
        subdir = 'thermal'
        pattern = f"PACE-{tile}-{{doy}}-{band_name}.bin"
    elif band_name.startswith('Band_'):
        subdir = 'aggregated'
        pattern = f"PACE-{tile}-{{doy}}-{band_name}.bin"
    elif band_name.startswith('wl_'):
        subdir = 'wavelengths'
        pattern = f"PACE-{tile}-{{doy}}-{band_name}.bin"
    else:
        raise ValueError(f"Unknown band type: {band_name}")

    band_dir = composite_dir / subdir

    for doy in COMPOSITE_DOYS:
        filename = pattern.format(doy=doy)
        filepath = band_dir / filename

        if filepath.exists():
            data = np.fromfile(filepath, dtype=np.int16).reshape(TILE_SIZE, TILE_SIZE)
            data = np.where(data == NO_DATA_INT, np.nan, data.astype(np.float32))

            # Don't rescale thermal - it's already in Kelvin or scaled Kelvin
            if band_name != BAND_THERMAL:
                data = data / SCALE_FACTOR_INPUT

            cube.append(data)
            doy_list.append(doy)
        else:
            logger.warning(f"Missing: {filepath}")
            cube.append(np.full((TILE_SIZE, TILE_SIZE), np.nan))
            doy_list.append(doy)

    return np.stack(cube, axis=0), doy_list


def load_wavelength_cube(composite_dir: Path, tile: str, wavelength: int) -> Tuple[np.ndarray, List[str]]:
    """Load all composites for a single wavelength."""
    return load_band_cube(composite_dir, tile, f"wl_{wavelength:04d}")


def load_all_bands(composite_dir: Path, tile: str) -> Dict[str, np.ndarray]:
    """Load all aggregated bands and thermal into a dictionary."""
    bands = {}

    for band in BANDS:
        bands[band], _ = load_band_cube(composite_dir, tile, band)
        logger.info(f"  Loaded {band}: {bands[band].shape}")

    bands[BAND_THERMAL], _ = load_band_cube(composite_dir, tile, BAND_THERMAL)
    logger.info(f"  Loaded {BAND_THERMAL}: {bands[BAND_THERMAL].shape}")

    return bands


print("Data loading functions defined")


# %% Cell 6: Sorting Functions
VERY_LOW_SORT_VALUE = -999999.0

def sort_by_ndvi(cube: np.ndarray, ndvi_cube: np.ndarray, ascending: bool = True) -> np.ndarray:
    """Sort a data cube by NDVI values along the time axis."""
    ndvi_sort = np.where(np.isnan(ndvi_cube), VERY_LOW_SORT_VALUE, ndvi_cube)
    sort_idx = np.argsort(ndvi_sort, axis=0) if ascending else np.argsort(-ndvi_sort, axis=0)
    return np.take_along_axis(cube, sort_idx, axis=0)


def sort_by_temperature(cube: np.ndarray, thermal_cube: np.ndarray, ascending: bool = True) -> np.ndarray:
    """Sort a data cube by temperature values along the time axis."""
    temp_sort = np.where(np.isnan(thermal_cube), VERY_LOW_SORT_VALUE, thermal_cube)
    sort_idx = np.argsort(temp_sort, axis=0) if ascending else np.argsort(-temp_sort, axis=0)
    return np.take_along_axis(cube, sort_idx, axis=0)


def sort_by_index(cube: np.ndarray, index_cube: np.ndarray, ascending: bool = True) -> np.ndarray:
    """Sort a data cube by any index values along the time axis."""
    idx_sort = np.where(np.isnan(index_cube), VERY_LOW_SORT_VALUE, index_cube)
    sort_idx = np.argsort(idx_sort, axis=0) if ascending else np.argsort(-idx_sort, axis=0)
    return np.take_along_axis(cube, sort_idx, axis=0)


print("Sorting functions defined")


# %% Cell 7: Basic Statistics Functions
def metric_min(cube: np.ndarray) -> np.ndarray:
    """Minimum value across composites."""
    with np.errstate(all='ignore'):
        return np.nanmin(cube, axis=0)


def metric_max(cube: np.ndarray) -> np.ndarray:
    """Maximum value across composites."""
    with np.errstate(all='ignore'):
        return np.nanmax(cube, axis=0)


def metric_median(cube: np.ndarray) -> np.ndarray:
    """Median value across composites."""
    with np.errstate(all='ignore'):
        return np.nanmedian(cube, axis=0)


def metric_mean(cube: np.ndarray) -> np.ndarray:
    """Mean value across composites."""
    with np.errstate(all='ignore'):
        return np.nanmean(cube, axis=0)


def metric_amplitude(cube: np.ndarray) -> np.ndarray:
    """Amplitude (max - min) across composites."""
    with np.errstate(all='ignore'):
        return np.nanmax(cube, axis=0) - np.nanmin(cube, axis=0)


def metric_mean_n(cube: np.ndarray, n: int, from_top: bool = True) -> np.ndarray:
    """
    Mean of top N or bottom N values, handling NaN properly.

    FIXED: NaN values are pushed to the opposite end during sorting so they
    don't contaminate the top/bottom N selection.
    """
    if from_top:
        # For "top N": push NaN to beginning (-inf) so they sort first
        sort_cube = np.where(np.isnan(cube), -np.inf, cube)
        sorted_cube = np.sort(sort_cube, axis=0)
        sorted_cube = np.where(sorted_cube == -np.inf, np.nan, sorted_cube)
        subset = sorted_cube[-n:, :, :]
    else:
        # For "bottom N": push NaN to end (+inf) so they sort last  
        sort_cube = np.where(np.isnan(cube), np.inf, cube)
        sorted_cube = np.sort(sort_cube, axis=0)
        sorted_cube = np.where(sorted_cube == np.inf, np.nan, sorted_cube)
        subset = sorted_cube[:n, :, :]

    with np.errstate(all='ignore'):
        return np.nanmean(subset, axis=0)


print("Basic statistics functions defined")

def mean_at_extreme(values: np.ndarray, key: np.ndarray, n: int, highest: bool = True) -> np.ndarray:
    """Mean of `values` at the n composites where `key` is highest (or lowest).

    v3 fix. Replaces two v2 patterns that silently computed something else:
      1. Sorting `values` by `key` and then calling metric_mean_n(), which
         re-sorts by `values` itself and discards the key order -- so e.g.
         EVI-HighChlorophyll3Mean was just "top-3 EVI".
      2. Pushing missing keys to one end of the sort and then taking that end
         -- so e.g. Warmest3MeanBandRefl picked composites with NO thermal
         observation as the "warmest".
    Only composites with a valid (finite) key are eligible. If fewer than n
    are valid, the mean uses those; if none are, the result is NaN.
    """
    valid = np.isfinite(key)
    k = np.where(valid, key, -np.inf if highest else np.inf)
    order = np.argsort(k, axis=0)
    if highest:
        order = order[::-1]
    sel = order[:n]
    v = np.take_along_axis(values, sel, axis=0)
    v = np.where(np.take_along_axis(valid, sel, axis=0), v, np.nan)
    with np.errstate(all='ignore'):
        return np.nanmean(v, axis=0)



def value_at_key_rank(values: np.ndarray, key: np.ndarray, rank: str) -> np.ndarray:
    """Value of `values` at the composite where `key` is 'lowest', 'median' or 'highest'.

    v4. Only composites where BOTH the key and the value are valid take part.
    'median' is element n_valid // 2 of the ascending key order (the upper
    middle when n_valid is even), which is what "reflectance associated with
    median greenness" means in the MODIS VCF metric list. NaN where no
    composite is valid.
    """
    valid = np.isfinite(key) & np.isfinite(values)
    k = np.where(valid, key, np.inf)          # invalid composites sort to the end
    order = np.argsort(k, axis=0, kind="stable")
    sorted_vals = np.take_along_axis(values, order, axis=0)
    n_valid = valid.sum(axis=0)
    if rank == "lowest":
        pos = np.zeros_like(n_valid)
    elif rank == "highest":
        pos = n_valid - 1
    elif rank == "median":
        pos = n_valid // 2
    else:
        raise ValueError(f"rank must be lowest, median or highest, not {rank!r}")
    pos = np.clip(pos, 0, values.shape[0] - 1)
    out = np.take_along_axis(sorted_vals, pos[np.newaxis, ...], axis=0)[0]
    return np.where(n_valid > 0, out, np.nan)


def amplitude_by_key(values: np.ndarray, key: np.ndarray) -> np.ndarray:
    """Value at the highest-key composite minus value at the lowest-key composite.

    v4. Signed: for key = NDVI this is "greenest minus least green". This is
    what AmpGreenest/AmpWarmest meant before a NaN "fix" replaced it with the
    plain max - min of the band (which ignores the key entirely).
    """
    return value_at_key_rank(values, key, "highest") - value_at_key_rank(values, key, "lowest")


def calculate_greenness_metrics(bands: Dict[str, np.ndarray], ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate all greenness-sorted metrics.
    FIXED: Proper NaN handling for MinGreenness and AmpGreenest.
    v4: MedianGreenness and AmpGreenest use the NDVI order (see header).
    """
    metrics = {}

    # Pre-compute valid NDVI count (used for masking)
    valid_count = np.sum(np.isfinite(ndvi_cube), axis=0)

    for band_name in BANDS:
        band_cube = bands[band_name]

        # For MaxGreenness: NaN NDVI -> -inf so they sort to beginning, take from end
        ndvi_for_max = np.where(np.isfinite(ndvi_cube), ndvi_cube, -np.inf)
        sort_idx_max = np.argsort(ndvi_for_max, axis=0)
        sorted_cube_max = np.take_along_axis(band_cube, sort_idx_max, axis=0)

        max_green = sorted_cube_max[-1, :, :]
        metrics[f'BandReflMaxGreenness-{band_name}'] = scale_reflectance(max_green)

        # For MinGreenness: NaN NDVI -> +inf so they sort to END, take from beginning
        ndvi_for_min = np.where(np.isfinite(ndvi_cube), ndvi_cube, np.inf)
        sort_idx_min = np.argsort(ndvi_for_min, axis=0)
        sorted_cube_min = np.take_along_axis(band_cube, sort_idx_min, axis=0)

        # Position 0 now has the value at lowest VALID NDVI
        min_green = sorted_cube_min[0, :, :]
        # Mask pixels with no valid NDVI
        min_green = np.where(valid_count > 0, min_green, np.nan)
        metrics[f'BandReflMinGreenness-{band_name}'] = scale_reflectance(min_green)

        # v4: band value at the median-NDVI composite (was the plain median)
        metrics[f'BandReflMedianGreenness-{band_name}'] = scale_reflectance(value_at_key_rank(band_cube, ndvi_cube, "median"))

        # v4: band at the greenest composite minus band at the least-green one (was plain max - min)
        metrics[f'AmpGreenestBandRefl-{band_name}'] = scale_reflectance(amplitude_by_key(band_cube, ndvi_cube))

        # Greenest N means
        metrics[f'Greenest3MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(band_cube, ndvi_cube, 3, highest=True))
        metrics[f'Greenest6MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(band_cube, ndvi_cube, 6, highest=True))
        metrics[f'Greenest8MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(band_cube, ndvi_cube, 8, highest=True))

    # Same for NDVI
    ndvi_for_max = np.where(np.isfinite(ndvi_cube), ndvi_cube, -np.inf)
    sort_idx_asc = np.argsort(ndvi_for_max, axis=0)
    sorted_ndvi_asc = np.take_along_axis(ndvi_cube, sort_idx_asc, axis=0)

    metrics['BandReflMaxGreenness-NDVI'] = scale_ndvi(sorted_ndvi_asc[-1, :, :])

    ndvi_for_min = np.where(np.isfinite(ndvi_cube), ndvi_cube, np.inf)
    sort_idx_min = np.argsort(ndvi_for_min, axis=0)
    sorted_ndvi_min = np.take_along_axis(ndvi_cube, sort_idx_min, axis=0)
    sorted_ndvi_min = np.where(sorted_ndvi_min == np.inf, np.nan, sorted_ndvi_min)

    valid_count = np.sum(np.isfinite(ndvi_cube), axis=0)
    min_ndvi = sorted_ndvi_min[0, :, :]
    min_ndvi = np.where(valid_count > 0, min_ndvi, np.nan)
    metrics['BandReflMinGreenness-NDVI'] = scale_ndvi(min_ndvi)

    metrics['BandReflMedianGreenness-NDVI'] = scale_ndvi(np.nanmedian(sorted_ndvi_asc, axis=0))

    metrics['AmpGreenestBandRefl-NDVI'] = scale_ndvi(
        np.nanmax(ndvi_cube, axis=0) - np.nanmin(ndvi_cube, axis=0)
    )

    sorted_ndvi = sort_by_ndvi(ndvi_cube, ndvi_cube, ascending=True)
    metrics['Greenest3MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 3, from_top=True))
    metrics['Greenest6MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 6, from_top=True))
    metrics['Greenest8MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 8, from_top=True))

    return metrics

# # %% Cell 8: Greenness-Sorted Metrics
# def calculate_greenness_metrics(bands: Dict[str, np.ndarray], ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
#     """
#     Calculate all greenness-sorted metrics.
#     Returns SCALED Int16 arrays.
#     """
#     metrics = {}

#     for band_name in BANDS:
#         sorted_cube = sort_by_ndvi(bands[band_name], ndvi_cube, ascending=True)

#         metrics[f'BandReflMaxGreenness-{band_name}'] = scale_reflectance(sorted_cube[-1, :, :])
#         metrics[f'BandReflMinGreenness-{band_name}'] = scale_reflectance(sorted_cube[0, :, :])
#         metrics[f'BandReflMedianGreenness-{band_name}'] = scale_reflectance(metric_median(sorted_cube))
#         metrics[f'AmpGreenestBandRefl-{band_name}'] = scale_reflectance(sorted_cube[-1, :, :] - sorted_cube[0, :, :])
#         metrics[f'Greenest3MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 3, from_top=True))
#         metrics[f'Greenest6MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 6, from_top=True))
#         metrics[f'Greenest8MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 8, from_top=True))

#     sorted_ndvi = sort_by_ndvi(ndvi_cube, ndvi_cube, ascending=True)
#     metrics['BandReflMaxGreenness-NDVI'] = scale_ndvi(sorted_ndvi[-1, :, :])
#     metrics['BandReflMinGreenness-NDVI'] = scale_ndvi(sorted_ndvi[0, :, :])
#     metrics['BandReflMedianGreenness-NDVI'] = scale_ndvi(metric_median(sorted_ndvi))
#     metrics['AmpGreenestBandRefl-NDVI'] = scale_ndvi(sorted_ndvi[-1, :, :] - sorted_ndvi[0, :, :])
#     metrics['Greenest3MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 3, from_top=True))
#     metrics['Greenest6MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 6, from_top=True))
#     metrics['Greenest8MeanBandRefl-NDVI'] = scale_ndvi(metric_mean_n(sorted_ndvi, 8, from_top=True))

#     return metrics


print("Greenness metrics defined")


# %% Cell 9: Thermal-Sorted Metrics (FIXED for NaN handling)
def calculate_thermal_sorted_metrics(bands: Dict[str, np.ndarray], ndvi_cube: np.ndarray, 
                                      thermal_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate all thermal-sorted metrics for optical bands.

    FIXES:
    - Handles missing thermal data by only sorting valid thermal observations
    - Falls back to optical-only sort when thermal is missing

    Returns SCALED Int16 arrays.
    """
    metrics = {}
    H, W = thermal_cube.shape[1], thermal_cube.shape[2]
    n_composites = thermal_cube.shape[0]

    # Check thermal coverage
    thermal_valid_per_pixel = np.sum(np.isfinite(thermal_cube), axis=0)
    min_thermal = np.min(thermal_valid_per_pixel)
    logger.info(f"  Calculating thermal-sorted metrics (min thermal obs: {min_thermal})")

    # Helper function: sort by temperature with NaN handling
    def sort_by_temperature_safe(data_cube, thermal_cube, ascending=True):
        """
        Sort data_cube by thermal_cube values, handling NaN in thermal.

        For pixels with partial thermal data, only valid thermal observations
        are used for sorting. NaN thermal values sort to the end.
        """
        # Replace NaN with -inf (will sort to beginning) or inf (sort to end)
        if ascending:
            thermal_for_sort = np.where(np.isfinite(thermal_cube), thermal_cube, np.inf)
        else:
            thermal_for_sort = np.where(np.isfinite(thermal_cube), thermal_cube, -np.inf)

        sort_idx = np.argsort(thermal_for_sort, axis=0)
        sorted_data = np.take_along_axis(data_cube, sort_idx, axis=0)

        return sorted_data

    # Thermal-sorted metrics for reflectance bands
    for band_name in BANDS:
        sorted_cube = sort_by_temperature_safe(bands[band_name], thermal_cube, ascending=True)

        # Use nanmean/nanmax to handle any remaining NaN
        metrics[f'BandReflMaxTemp-{band_name}'] = scale_reflectance(mean_at_extreme(bands[band_name], thermal_cube, 1, highest=True))
        metrics[f'BandReflMinTemp-{band_name}'] = scale_reflectance(mean_at_extreme(bands[band_name], thermal_cube, 1, highest=False))
        # v4: value at the median-temperature composite, and warmest minus coolest
        metrics[f'BandReflMedianTemp-{band_name}'] = scale_reflectance(value_at_key_rank(bands[band_name], thermal_cube, "median"))
        metrics[f'AmpWarmestBandRefl-{band_name}'] = scale_reflectance(amplitude_by_key(bands[band_name], thermal_cube))
        metrics[f'Warmest3MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(bands[band_name], thermal_cube, 3, highest=True))
        metrics[f'Warmest6MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(bands[band_name], thermal_cube, 6, highest=True))
        metrics[f'Warmest8MeanBandRefl-{band_name}'] = scale_reflectance(mean_at_extreme(bands[band_name], thermal_cube, 8, highest=True))

    # Thermal-sorted NDVI
    sorted_ndvi = sort_by_temperature_safe(ndvi_cube, thermal_cube, ascending=True)
    metrics['BandReflMaxTemp-NDVI'] = scale_ndvi(mean_at_extreme(ndvi_cube, thermal_cube, 1, highest=True))
    metrics['BandReflMinTemp-NDVI'] = scale_ndvi(mean_at_extreme(ndvi_cube, thermal_cube, 1, highest=False))
    metrics['BandReflMedianTemp-NDVI'] = scale_ndvi(value_at_key_rank(ndvi_cube, thermal_cube, "median"))
    metrics['AmpWarmestBandRefl-NDVI'] = scale_ndvi(amplitude_by_key(ndvi_cube, thermal_cube))
    metrics['Warmest3MeanBandRefl-NDVI'] = scale_ndvi(mean_at_extreme(ndvi_cube, thermal_cube, 3, highest=True))
    metrics['Warmest6MeanBandRefl-NDVI'] = scale_ndvi(mean_at_extreme(ndvi_cube, thermal_cube, 6, highest=True))
    metrics['Warmest8MeanBandRefl-NDVI'] = scale_ndvi(mean_at_extreme(ndvi_cube, thermal_cube, 8, highest=True))

    # Temperature at greenest (sorted by NDVI)
    ndvi_for_sort = np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube)
    sort_idx = np.argsort(ndvi_for_sort, axis=0)
    thermal_sorted_by_ndvi = np.take_along_axis(thermal_cube, sort_idx, axis=0)
    greenest3_thermal = thermal_sorted_by_ndvi[-3:, :, :]

    # Use nanmean and fallback to overall mean if all NaN
    temp_greenest3 = np.nanmean(greenest3_thermal, axis=0)
    temp_greenest3 = np.where(np.isfinite(temp_greenest3), temp_greenest3, np.nanmean(thermal_cube, axis=0))
    metrics['TempMeanGreenest3'] = scale_thermal(temp_greenest3)

    # Temperature sorted by temperature (warmest)
    thermal_for_sort = np.where(np.isnan(thermal_cube), -np.inf, thermal_cube)
    sort_idx_temp = np.argsort(thermal_for_sort, axis=0)
    thermal_sorted_by_temp = np.take_along_axis(thermal_cube, sort_idx_temp, axis=0)
    warmest3_thermal = thermal_sorted_by_temp[-3:, :, :]

    temp_warmest3 = np.nanmean(warmest3_thermal, axis=0)
    temp_warmest3 = np.where(np.isfinite(temp_warmest3), temp_warmest3, np.nanmean(thermal_cube, axis=0))
    metrics['TempMeanWarmest3'] = scale_thermal(temp_warmest3)

    return metrics


print("Thermal-sorted metrics defined (FIXED)")


# %% Cell 9b: Band31 Basic Metrics (FIXED for NaN handling)
def calculate_band31_basic_metrics(thermal_cube: np.ndarray, 
                                    ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate basic statistics for Band31 (thermal/VIIRS LST).

    These are CRITICAL for bare ground detection:
    - Bare ground = hot (high thermal)
    - Forest = cooler (lower thermal due to evapotranspiration)
    - Water = cold

    FIXES:
    - When indexing specific composites (peak NDVI, min NDVI), falls back to
      mean thermal if that specific composite has no data
    - Sorting handles NaN values properly

    Returns SCALED Int16 arrays (× 100 for Kelvin).
    """
    metrics = {}
    H, W = thermal_cube.shape[1], thermal_cube.shape[2]
    n_composites = thermal_cube.shape[0]

    logger.info("  Calculating Band31 (thermal) basic metrics...")

    # Check thermal coverage
    thermal_valid = np.isfinite(thermal_cube)
    thermal_coverage = np.sum(thermal_valid) / thermal_valid.size
    valid_per_pixel = np.sum(thermal_valid, axis=0)
    logger.info(f"    Thermal coverage: {100*thermal_coverage:.1f}%")
    logger.info(f"    Valid obs per pixel: min={valid_per_pixel.min()}, max={valid_per_pixel.max()}, mean={valid_per_pixel.mean():.1f}")

    # Pre-compute the overall thermal mean for fallback
    thermal_mean = np.nanmean(thermal_cube, axis=0)

    # Basic statistics (these handle NaN well with nanmin/nanmax)
    metrics['BandReflMin-Band31'] = scale_thermal(np.nanmin(thermal_cube, axis=0))
    metrics['BandReflMax-Band31'] = scale_thermal(np.nanmax(thermal_cube, axis=0))
    metrics['BandReflMean-Band31'] = scale_thermal(thermal_mean)
    metrics['BandReflMedian-Band31'] = scale_thermal(np.nanmedian(thermal_cube, axis=0))
    metrics['AmpBandRefl-Band31'] = scale_thermal_diff(
        np.nanmax(thermal_cube, axis=0) - np.nanmin(thermal_cube, axis=0)
    )

    # =========================================================================
    # Temperature-sorted thermal (warmest/coolest)
    # Sort with NaN handling: -inf for NaN when finding warmest, +inf for coolest
    # =========================================================================

    # For WARMEST: replace NaN with -inf so they sort to beginning (ignored)
    thermal_for_warmest = np.where(np.isfinite(thermal_cube), thermal_cube, -np.inf)
    thermal_sorted_desc = np.sort(thermal_for_warmest, axis=0)[::-1, :, :]  # Descending
    thermal_sorted_desc = np.where(thermal_sorted_desc == -np.inf, np.nan, thermal_sorted_desc)

    # Warmest N (high thermal = likely bare/dry)
    metrics['Warmest3MeanBandRefl-Band31'] = scale_thermal(np.nanmean(thermal_sorted_desc[:3, :, :], axis=0))
    metrics['Warmest6MeanBandRefl-Band31'] = scale_thermal(np.nanmean(thermal_sorted_desc[:6, :, :], axis=0))
    metrics['Warmest8MeanBandRefl-Band31'] = scale_thermal(np.nanmean(thermal_sorted_desc[:8, :, :], axis=0))

    # For COOLEST: replace NaN with +inf so they sort to end (ignored)
    thermal_for_coolest = np.where(np.isfinite(thermal_cube), thermal_cube, np.inf)
    thermal_sorted_asc = np.sort(thermal_for_coolest, axis=0)  # Ascending
    thermal_sorted_asc = np.where(thermal_sorted_asc == np.inf, np.nan, thermal_sorted_asc)

    # Coolest N (low thermal = likely vegetated/wet)
    metrics['Coolest3MeanBandRefl-Band31'] = scale_thermal(np.nanmean(thermal_sorted_asc[:3, :, :], axis=0))
    metrics['Coolest6MeanBandRefl-Band31'] = scale_thermal(np.nanmean(thermal_sorted_asc[:6, :, :], axis=0))

    # =========================================================================
    # Greenness-sorted thermal (thermal at greenest/brownest NDVI)
    # =========================================================================
    ndvi_sort_idx = np.argsort(np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube), axis=0)
    thermal_sorted_by_ndvi = np.take_along_axis(thermal_cube, ndvi_sort_idx, axis=0)

    # Thermal at greenest 3 composites (with fallback)
    greenest3_thermal = np.nanmean(thermal_sorted_by_ndvi[-3:, :, :], axis=0)
    greenest3_thermal = np.where(np.isfinite(greenest3_thermal), greenest3_thermal, thermal_mean)
    metrics['Greenest3MeanBandRefl-Band31'] = scale_thermal(greenest3_thermal)

    # Thermal at brownest 3 composites (with fallback)
    brownest3_thermal = np.nanmean(thermal_sorted_by_ndvi[:3, :, :], axis=0)
    brownest3_thermal = np.where(np.isfinite(brownest3_thermal), brownest3_thermal, thermal_mean)
    metrics['Lowest3MeanBandRefl-Band31'] = scale_thermal(brownest3_thermal)

    # =========================================================================
    # Thermal at specific phenology points (with fallback for missing data)
    # =========================================================================
    i_idx = np.arange(H)[:, np.newaxis]
    j_idx = np.arange(W)[np.newaxis, :]

    # Thermal at peak NDVI (single composite) - WITH FALLBACK
    peak_ndvi_idx = np.argmax(np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube), axis=0)
    thermal_at_peak = thermal_cube[peak_ndvi_idx, i_idx, j_idx]
    # Fallback: use mean thermal if the specific composite has no data
    thermal_at_peak = np.where(np.isfinite(thermal_at_peak), thermal_at_peak, thermal_mean)
    metrics['ThermalAtPeakNDVI-Band31'] = scale_thermal(thermal_at_peak)

    # Thermal at minimum NDVI - WITH FALLBACK
    min_ndvi_idx = np.argmin(np.where(np.isnan(ndvi_cube), np.inf, ndvi_cube), axis=0)
    thermal_at_min = thermal_cube[min_ndvi_idx, i_idx, j_idx]
    thermal_at_min = np.where(np.isfinite(thermal_at_min), thermal_at_min, thermal_mean)
    metrics['ThermalAtMinNDVI-Band31'] = scale_thermal(thermal_at_min)

    # Thermal range at greenest vs brownest (high for deciduous, low for evergreen)
    thermal_green_brown_diff = greenest3_thermal - brownest3_thermal
    metrics['ThermalGreenBrownDiff-Band31'] = scale_thermal_diff(thermal_green_brown_diff)

    logger.info(f"    Added {len(metrics)} Band31 metrics")

    return metrics


print("Band31 basic metrics defined (FIXED)")


# %% Cell 9c: Snow Detection Metrics (FIXED for NaN handling)
def calculate_snow_metrics(band3_cube: np.ndarray, 
                           band4_cube: np.ndarray,
                           band7_cube: np.ndarray,
                           ndvi_cube: np.ndarray,
                           thermal_cube: np.ndarray) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """
    Detect snow contamination and calculate snow-aware metrics.

    FIXES:
    - Handles missing thermal data by using first valid value or mean
    - No-snow regions get valid values (not NaN from missing first composite)
    """
    metrics = {}
    H, W = ndvi_cube.shape[1], ndvi_cube.shape[2]
    n_composites = ndvi_cube.shape[0]

    logger.info("  Calculating snow detection metrics...")

    # ... [NDSI calculation and snow mask - keep as before] ...

    with np.errstate(divide='ignore', invalid='ignore'):
        ndsi = (band4_cube - band7_cube) / (band4_cube + band7_cube + 0.0001)
        ndsi = np.where(np.isfinite(ndsi), ndsi, np.nan)

    snow_mask = ndsi > 0.4

    # Basic snow metrics
    snow_count = np.sum(snow_mask, axis=0).astype(np.int16)
    metrics['Snow-CompositeCount'] = snow_count

    valid_mask = np.isfinite(ndvi_cube)
    snow_free_count = np.sum((~snow_mask) & valid_mask, axis=0).astype(np.int16)
    metrics['Snow-FreeCompositeCount'] = snow_free_count

    metrics['Snow-MaxNDSI'] = scale_index(np.nanmax(ndsi, axis=0))

    # Snow at brownest
    brownest_idx = np.argmin(np.where(np.isnan(ndvi_cube), np.inf, ndvi_cube), axis=0)
    i_idx = np.arange(H)[:, np.newaxis]
    j_idx = np.arange(W)[np.newaxis, :]
    snow_at_brownest = snow_mask[brownest_idx, i_idx, j_idx]
    metrics['Snow-AtBrownest'] = snow_at_brownest.astype(np.int16)

    # Determine snow region
    total_obs = np.prod(snow_mask.shape)
    snow_obs = np.sum(snow_mask)
    snow_pct = 100 * snow_obs / total_obs
    is_snow_region = snow_pct >= 1.0

    logger.info(f"    Snow coverage: {snow_pct:.1f}% - {'SNOW REGION' if is_snow_region else 'NO-SNOW REGION'}")

    # =========================================================================
    # HELPER: Get first valid value across time dimension
    # =========================================================================
    def get_first_valid(cube):
        """Get first valid (non-NaN) value for each pixel across time."""
        result = np.full((H, W), np.nan, dtype=np.float32)
        for t in range(cube.shape[0]):
            needs_fill = np.isnan(result) & np.isfinite(cube[t, :, :])
            result = np.where(needs_fill, cube[t, :, :], result)
            if np.all(np.isfinite(result)):
                break
        # Fallback to mean if still NaN
        result = np.where(np.isfinite(result), result, np.nanmean(cube, axis=0))
        return result

    # =========================================================================
    logger.info("  Calculating snow-free metrics...")

    if is_snow_region:
        # SNOW REGION: mask out snow composites
        snow_free_mask = (~snow_mask) & np.isfinite(ndvi_cube)

        # Snow-free band metrics
        for band_name, band_cube in [('Band_7', band7_cube)]:
            band_sf = np.where(snow_free_mask, band_cube, np.nan)
            metrics[f'SnowFree-{band_name}-Mean'] = scale_reflectance(np.nanmean(band_sf, axis=0))
            metrics[f'SnowFree-{band_name}-Max'] = scale_reflectance(np.nanmax(band_sf, axis=0))
            metrics[f'SnowFree-{band_name}-Min'] = scale_reflectance(np.nanmin(band_sf, axis=0))
            metrics[f'SnowFree-{band_name}-Amp'] = scale_reflectance(
                np.nanmax(band_sf, axis=0) - np.nanmin(band_sf, axis=0)
            )

        # Snow-free NDVI
        ndvi_sf = np.where(snow_free_mask, ndvi_cube, np.nan)
        metrics['SnowFree-NDVI-Max'] = scale_ndvi(np.nanmax(ndvi_sf, axis=0))
        metrics['SnowFree-NDVI-Min'] = scale_ndvi(np.nanmin(ndvi_sf, axis=0))
        metrics['SnowFree-NDVI-Median'] = scale_ndvi(np.nanmedian(ndvi_sf, axis=0))

        sort_ndvi_sf = np.where(np.isnan(ndvi_sf), np.inf, ndvi_sf)
        sorted_ndvi_sf = np.sort(sort_ndvi_sf, axis=0)
        sorted_ndvi_sf = np.where(sorted_ndvi_sf == np.inf, np.nan, sorted_ndvi_sf)
        metrics['SnowFree-NDVI-Brownest3Mean'] = scale_ndvi(np.nanmean(sorted_ndvi_sf[:3], axis=0))

        # Snow-free Band7 at brownest
        ndvi_sf_sort_idx = np.argsort(np.where(np.isnan(ndvi_sf), -np.inf, ndvi_sf), axis=0)
        band7_sf = np.where(snow_free_mask, band7_cube, np.nan)
        metrics['SnowFree-Lowest3MeanBandRefl-Band_7'] = scale_reflectance(mean_at_extreme(band7_sf, ndvi_sf, 3, highest=False))

        # Snow-free thermal
        thermal_sf = np.where(snow_free_mask, thermal_cube, np.nan)
        metrics['SnowFree-LST-Max'] = scale_thermal(np.nanmax(thermal_sf, axis=0))
        metrics['SnowFree-LST-Min'] = scale_thermal(np.nanmin(thermal_sf, axis=0))
        metrics['SnowFree-LST-Mean'] = scale_thermal(np.nanmean(thermal_sf, axis=0))

        # First snow-free composite
        first_sf = np.argmax(snow_free_mask, axis=0).astype(np.float32)
        never_sf = ~np.any(snow_free_mask, axis=0)
        first_sf = np.where(never_sf, np.nan, first_sf)

        metrics['SnowFree-FirstComposite'] = np.where(
            np.isfinite(first_sf), (first_sf + 1).astype(np.int16), NO_DATA_INT
        ).astype(np.int16)

        # LST and NDVI at first snow-free (with fallback)
        first_idx = np.clip(np.nan_to_num(first_sf, nan=0).astype(int), 0, n_composites - 1)

        lst_at_sf = thermal_cube[first_idx, i_idx, j_idx]
        lst_at_sf = np.where(np.isfinite(first_sf), lst_at_sf, np.nan)
        # FALLBACK: if still NaN, use mean thermal
        lst_at_sf = np.where(np.isfinite(lst_at_sf), lst_at_sf, np.nanmean(thermal_cube, axis=0))
        metrics['LST-AtFirstSnowFree'] = scale_thermal(lst_at_sf)

        ndvi_at_sf = ndvi_cube[first_idx, i_idx, j_idx]
        ndvi_at_sf = np.where(np.isfinite(first_sf), ndvi_at_sf, np.nan)
        ndvi_at_sf = np.where(np.isfinite(ndvi_at_sf), ndvi_at_sf, np.nanmean(ndvi_cube, axis=0))
        metrics['NDVI-AtFirstSnowFree'] = scale_ndvi(ndvi_at_sf)

    else:
        # NO-SNOW REGION: everything is "snow-free"
        logger.info("    No-snow region - using full-year values with NaN fallbacks")

        # Band metrics = regular metrics
        metrics['SnowFree-Band_7-Mean'] = scale_reflectance(np.nanmean(band7_cube, axis=0))
        metrics['SnowFree-Band_7-Max'] = scale_reflectance(np.nanmax(band7_cube, axis=0))
        metrics['SnowFree-Band_7-Min'] = scale_reflectance(np.nanmin(band7_cube, axis=0))
        metrics['SnowFree-Band_7-Amp'] = scale_reflectance(
            np.nanmax(band7_cube, axis=0) - np.nanmin(band7_cube, axis=0)
        )

        # NDVI metrics
        metrics['SnowFree-NDVI-Max'] = scale_ndvi(np.nanmax(ndvi_cube, axis=0))
        metrics['SnowFree-NDVI-Min'] = scale_ndvi(np.nanmin(ndvi_cube, axis=0))
        metrics['SnowFree-NDVI-Median'] = scale_ndvi(np.nanmedian(ndvi_cube, axis=0))

        sort_ndvi = np.where(np.isnan(ndvi_cube), np.inf, ndvi_cube)
        sorted_ndvi = np.sort(sort_ndvi, axis=0)
        sorted_ndvi = np.where(sorted_ndvi == np.inf, np.nan, sorted_ndvi)
        metrics['SnowFree-NDVI-Brownest3Mean'] = scale_ndvi(np.nanmean(sorted_ndvi[:3], axis=0))

        ndvi_sort_idx = np.argsort(np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube), axis=0)
        metrics['SnowFree-Lowest3MeanBandRefl-Band_7'] = scale_reflectance(mean_at_extreme(band7_cube, ndvi_cube, 3, highest=False))

        # Thermal metrics - USE FIRST VALID, NOT FIRST COMPOSITE
        metrics['SnowFree-LST-Max'] = scale_thermal(np.nanmax(thermal_cube, axis=0))
        metrics['SnowFree-LST-Min'] = scale_thermal(np.nanmin(thermal_cube, axis=0))
        metrics['SnowFree-LST-Mean'] = scale_thermal(np.nanmean(thermal_cube, axis=0))

        # First composite = 1 (always snow-free)
        metrics['SnowFree-FirstComposite'] = np.ones((H, W), dtype=np.int16)

        # LST/NDVI at "first snow-free" = first VALID value (not first composite)
        metrics['LST-AtFirstSnowFree'] = scale_thermal(get_first_valid(thermal_cube))
        metrics['NDVI-AtFirstSnowFree'] = scale_ndvi(get_first_valid(ndvi_cube))

    logger.info(f"    Added {len(metrics)} snow metrics")
    return metrics, snow_mask

print("Snow detection metrics defined (FIXED for no-snow regions)")



# %% Cell 9d: QA Observation Count Metrics (NEW - Diagnostic Only)
def calculate_qa_observation_metrics(bands: Dict[str, np.ndarray],
                                      thermal_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate observation count metrics for diagnostic purposes.

    These metrics track data quality and should NOT be used in the model
    (they don't represent land surface properties).

    Prefix with 'QA_' to easily exclude from training features.
    """
    metrics = {}

    logger.info("  Calculating QA observation count metrics (diagnostic only)...")

    # Count valid observations per pixel for optical (using Band_1)
    band1_cube = bands['Band_1']
    optical_valid = np.isfinite(band1_cube)
    optical_count = np.sum(optical_valid, axis=0).astype(np.int16)

    # Count valid observations for thermal
    thermal_valid = np.isfinite(thermal_cube)
    thermal_count = np.sum(thermal_valid, axis=0).astype(np.int16)

    # QA metrics (prefix with QA_ to exclude from model)
    metrics['QA_ObsCount-Optical-Total'] = optical_count
    metrics['QA_ObsCount-Optical-Min'] = np.min(optical_valid.astype(np.int16), axis=0)

    metrics['QA_ObsCount-Thermal-Total'] = thermal_count
    metrics['QA_ObsCount-Thermal-Min'] = np.min(thermal_valid.astype(np.int16), axis=0)

    # Difference (optical usually has more coverage than thermal)
    metrics['QA_ObsCount-OpticalMinusThermal'] = (optical_count - thermal_count).astype(np.int16)

    # Count of periods with zero optical data
    zero_optical_periods = np.sum(~optical_valid, axis=0).astype(np.int16)
    metrics['QA_ObsCount-ZeroOpticalPeriods'] = zero_optical_periods

    # Count of periods with zero thermal data
    zero_thermal_periods = np.sum(~thermal_valid, axis=0).astype(np.int16)
    metrics['QA_ObsCount-ZeroThermalPeriods'] = zero_thermal_periods

    logger.info(f"    Added {len(metrics)} QA metrics")

    return metrics


print("QA observation count metrics defined (NEW - diagnostic only)")


# %% Cell 10: Basic Reflectance Metrics
def calculate_basic_metrics(bands: Dict[str, np.ndarray], ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate basic min/max/median/amplitude metrics for reflectance bands.
    Returns SCALED Int16 arrays.
    """
    metrics = {}

    for band_name in BANDS:
        cube = bands[band_name]
        metrics[f'BandReflMin-{band_name}'] = scale_reflectance(metric_min(cube))
        metrics[f'BandReflMax-{band_name}'] = scale_reflectance(metric_max(cube))
        metrics[f'BandReflMedian-{band_name}'] = scale_reflectance(metric_median(cube))
        metrics[f'AmpBandRefl-{band_name}'] = scale_reflectance(metric_amplitude(cube))

    metrics['BandReflMin-NDVI'] = scale_ndvi(metric_min(ndvi_cube))
    metrics['BandReflMax-NDVI'] = scale_ndvi(metric_max(ndvi_cube))
    metrics['BandReflMedian-NDVI'] = scale_ndvi(metric_median(ndvi_cube))
    metrics['AmpBandRefl-NDVI'] = scale_ndvi(metric_amplitude(ndvi_cube))

    return metrics


def calculate_lowest_n_metrics(bands: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Calculate lowest N mean reflectance metrics (brownest composites).
    Returns SCALED Int16 arrays.

    FIXED: Proper NaN handling in sort.
    """
    metrics = {}

    for band_name in BANDS:
        cube = bands[band_name]

        # FIXED: Push NaN to end (+inf) so lowest values are at beginning
        sort_cube = np.where(np.isnan(cube), np.inf, cube)
        sorted_cube = np.sort(sort_cube, axis=0)
        sorted_cube = np.where(sorted_cube == np.inf, np.nan, sorted_cube)

        metrics[f'Lowest3MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 3, from_top=False))
        metrics[f'Lowest6MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 6, from_top=False))
        metrics[f'Lowest8MeanBandRefl-{band_name}'] = scale_reflectance(metric_mean_n(sorted_cube, 8, from_top=False))

    return metrics


print("Basic reflectance metrics defined")


# %% Cell 11: Unsorted Monthly Metrics
def calculate_unsorted_monthly(bands: Dict[str, np.ndarray], ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate unsorted monthly bands (raw temporal data).
    Returns SCALED Int16 arrays.

    Note: These are NOT recommended for use in the model as they are 
    calendar-dependent and not hemisphere-agnostic.
    """
    metrics = {}

    for band_name in BANDS:
        cube = bands[band_name]
        for i, doy in enumerate(COMPOSITE_DOYS):
            metrics[f'UnsortedMonthly-{band_name}-{doy}'] = scale_reflectance(cube[i, :, :])

    for i, doy in enumerate(COMPOSITE_DOYS):
        metrics[f'UnsortedMonthly-NDVI-{doy}'] = scale_ndvi(ndvi_cube[i, :, :])

    return metrics


print("Unsorted monthly metrics defined")


# %% Cell 12: PACE-Enhanced Vegetation Indices (FIXED NaN handling)
def calculate_pace_indices(composite_dir: Path, tile: str, ndvi_cube: np.ndarray) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Calculate PACE-specific vegetation indices from hyperspectral wavelengths.

    FIXED: Proper NaN handling for all sorted metrics including AmpGreenness.

    Indices calculated:
    - EVI, NDWI, PRI, CIRE, NDRE, GCI, MTCI, CCI, mARI, NDII
    - REP (Red Edge Position)
    - REIP (Red Edge Inflection Point)
    """
    metrics = {}
    index_cubes = {}

    def load_wl(wl):
        cube, _ = load_wavelength_cube(composite_dir, tile, wl)
        return cube

    logger.info("  Loading wavelengths for PACE indices...")

    try:
        # Core wavelengths
        blue_469 = load_wl(470)
        green_550 = load_wl(550)
        red_645 = load_wl(645)
        red_670 = load_wl(670)
        rededge_705 = load_wl(704)
        rededge_720 = load_wl(719)
        rededge_750 = load_wl(752)
        nir_865 = load_wl(865)
        swir_1240 = load_wl(1249)
        swir_1640 = load_wl(1618)
        green_531 = load_wl(530)
        green_570 = load_wl(570)
        red_700 = load_wl(699)
        nir_780 = load_wl(754)

        # REP/REIP wavelengths
        rededge_680 = load_wl(682)
        rededge_740 = load_wl(742)
        rededge_760 = load_wl(754)

    except Exception as e:
        logger.warning(f"Error loading wavelengths for PACE indices: {e}")
        return metrics, index_cubes

    logger.info("  Calculating PACE indices...")

    with np.errstate(all='ignore'):
        # EVI: Enhanced Vegetation Index
        evi = 2.5 * (nir_865 - red_645) / (nir_865 + 6*red_645 - 7.5*blue_469 + 1)
        evi = np.where(np.isfinite(evi), np.clip(evi, -1, 1), np.nan)

        # NDWI: Normalized Difference Water Index
        ndwi = (nir_865 - swir_1240) / (nir_865 + swir_1240)
        ndwi = np.where(np.isfinite(ndwi), ndwi, np.nan)

        # PRI: Photochemical Reflectance Index
        pri = (green_531 - green_570) / (green_531 + green_570)
        pri = np.where(np.isfinite(pri), pri, np.nan)

        # CIRE: Chlorophyll Index Red-Edge
        cire = (nir_865 / rededge_705) - 1
        cire = np.where(np.isfinite(cire), cire, np.nan)

        # NDRE: Normalized Difference Red-Edge
        ndre = (nir_865 - rededge_720) / (nir_865 + rededge_720)
        ndre = np.where(np.isfinite(ndre), ndre, np.nan)

        # GCI: Green Chlorophyll Index
        gci = (nir_865 / green_550) - 1
        gci = np.where(np.isfinite(gci), gci, np.nan)

        # MTCI: MERIS Terrestrial Chlorophyll Index
        mtci = (rededge_750 - rededge_705) / (rededge_705 - red_670)
        mtci = np.where(np.isfinite(mtci), mtci, np.nan)

        # CCI: Chlorophyll-Carotenoid Index
        cci = (green_531 - red_645) / (green_531 + red_645)
        cci = np.where(np.isfinite(cci), cci, np.nan)

        # mARI: Modified Anthocyanin Reflectance Index
        mari = ((1/green_550) - (1/red_700)) * nir_780
        mari = np.where(np.isfinite(mari), mari, np.nan)

        # NDII: Normalized Difference Infrared Index
        ndii = (nir_865 - swir_1640) / (nir_865 + swir_1640)
        ndii = np.where(np.isfinite(ndii), ndii, np.nan)

        # REP: Red Edge Position
        logger.info("  Calculating Red Edge Position (REP)...")
        n_composites = evi.shape[0]
        rep_cube = np.full_like(evi, np.nan, dtype=np.float32)

        for i in range(n_composites):
            r_rep = (red_670[i] + nir_780[i]) / 2.0
            denominator = rededge_740[i] - rededge_705[i]
            denominator = np.where(np.abs(denominator) < 1e-10, 1e-10, denominator)
            rep = 700.0 + 40.0 * ((r_rep - rededge_705[i]) / denominator)
            rep = np.clip(rep, 680, 760)
            rep_cube[i] = np.where(np.isfinite(rep), rep, np.nan)

        # REIP: Red Edge Inflection Point
        logger.info("  Calculating Red Edge Inflection Point (REIP)...")
        reip_cube = np.full_like(evi, np.nan, dtype=np.float32)

        for i in range(n_composites):
            d693 = (rededge_705[i] - rededge_680[i]) / 22.0
            d712 = (rededge_720[i] - rededge_705[i]) / 15.0
            d731 = (rededge_740[i] - rededge_720[i]) / 23.0
            d748 = (rededge_760[i] - rededge_740[i]) / 12.0

            derivatives = np.stack([d693, d712, d731, d748], axis=0)
            wavelengths = np.array([693, 712, 731, 748])
            max_idx = np.argmax(derivatives, axis=0)
            reip_cube[i] = wavelengths[max_idx].astype(np.float32)

    # Store raw cubes for alternative sorting
    index_cubes = {
        'EVI': evi, 'NDWI': ndwi, 'PRI': pri, 'CIRE': cire, 'NDRE': ndre,
        'GCI': gci, 'MTCI': mtci, 'CCI': cci, 'mARI': mari, 'NDII': ndii,
        'REP': rep_cube, 'REIP': reip_cube
    }

    # =========================================================================
    # Standard metrics for all indices - FIXED NaN handling
    # =========================================================================
    standard_indices = ['EVI', 'NDWI', 'PRI', 'CIRE', 'NDRE', 'GCI', 'MTCI', 'CCI', 'mARI', 'NDII']

    for idx_name in standard_indices:
        idx_cube = index_cubes[idx_name]

        # Basic statistics (these already handle NaN correctly)
        metrics[f'PACEIndex-{idx_name}-Min'] = scale_index(metric_min(idx_cube))
        metrics[f'PACEIndex-{idx_name}-Max'] = scale_index(metric_max(idx_cube))
        metrics[f'PACEIndex-{idx_name}-Median'] = scale_index(metric_median(idx_cube))
        metrics[f'PACEIndex-{idx_name}-Amp'] = scale_index(metric_amplitude(idx_cube))

        # FIXED: Greenest3Mean with proper NaN handling
        # Push NaN to beginning (-inf) so they sort first, then take top 3
        sort_cube = np.where(np.isnan(idx_cube), -np.inf, idx_cube)
        sorted_idx = np.sort(sort_cube, axis=0)
        sorted_idx = np.where(sorted_idx == -np.inf, np.nan, sorted_idx)

        # v4: renamed from -Greenest3Mean. It is the mean of the index's own 3 highest
        # values, not the index at the 3 greenest (highest-NDVI) composites.
        metrics[f'PACEIndex-{idx_name}-Highest3Mean'] = scale_index(metric_mean_n(sorted_idx, 3, from_top=True))

        # v4: index at the greenest (highest-NDVI) composite minus index at the
        # least-green one. Was the plain max - min, identical to -Amp.
        metrics[f'PACEIndex-{idx_name}-AmpGreenness'] = scale_index(amplitude_by_key(idx_cube, ndvi_cube))

    # =========================================================================
    # REP metrics - FIXED NaN handling
    # =========================================================================
    metrics['PACEIndex-REP-Min'] = scale_rep(metric_min(rep_cube))
    metrics['PACEIndex-REP-Max'] = scale_rep(metric_max(rep_cube))
    metrics['PACEIndex-REP-Median'] = scale_rep(metric_median(rep_cube))
    metrics['PACEIndex-REP-Mean'] = scale_rep(np.nanmean(rep_cube, axis=0))
    metrics['PACEIndex-REP-Amp'] = scale_rep(metric_max(rep_cube) - metric_min(rep_cube))

    # FIXED: REP sorted metrics
    sort_rep = np.where(np.isnan(rep_cube), -np.inf, rep_cube)
    sorted_rep = np.sort(sort_rep, axis=0)
    sorted_rep = np.where(sorted_rep == -np.inf, np.nan, sorted_rep)

    metrics['PACEIndex-REP-Highest3Mean'] = scale_rep(metric_mean_n(sorted_rep, 3, from_top=True))  # v4: was -Greenest3Mean
    # v4: renamed from -Brownest3Mean (lowest 3 REP values; the NDVI-sorted Brownest3Mean is in the AltSort file)
    metrics['PACEIndex-REP-Lowest3Mean'] = scale_rep(metric_mean_n(sorted_rep, 3, from_top=False))

    # =========================================================================
    # REIP metrics - FIXED NaN handling
    # =========================================================================
    metrics['PACEIndex-REIP-Min'] = scale_rep(metric_min(reip_cube))
    metrics['PACEIndex-REIP-Max'] = scale_rep(metric_max(reip_cube))
    metrics['PACEIndex-REIP-Median'] = scale_rep(metric_median(reip_cube))
    metrics['PACEIndex-REIP-Mean'] = scale_rep(np.nanmean(reip_cube, axis=0))
    metrics['PACEIndex-REIP-Amp'] = scale_rep(metric_max(reip_cube) - metric_min(reip_cube))

    # FIXED: REIP sorted metrics
    sort_reip = np.where(np.isnan(reip_cube), -np.inf, reip_cube)
    sorted_reip = np.sort(sort_reip, axis=0)
    sorted_reip = np.where(sorted_reip == -np.inf, np.nan, sorted_reip)

    metrics['PACEIndex-REIP-Highest3Mean'] = scale_rep(metric_mean_n(sorted_reip, 3, from_top=True))  # v4: was -Greenest3Mean
    # v4: renamed from -Brownest3Mean (see REP above)
    metrics['PACEIndex-REIP-Lowest3Mean'] = scale_rep(metric_mean_n(sorted_reip, 3, from_top=False))

    # =========================================================================
    # Unsorted monthly indices (no NaN fix needed - direct indexing)
    # =========================================================================
    for idx_name in ['EVI', 'NDWI', 'PRI', 'CIRE', 'NDRE', 'GCI']:
        idx_cube = index_cubes[idx_name]
        for i, doy in enumerate(COMPOSITE_DOYS):
            metrics[f'UnsortedMonthlyIndex-{idx_name}-{doy}'] = scale_index(idx_cube[i, :, :])

    return metrics, index_cubes


print("PACE indices defined (FIXED NaN handling)")


# %% Cell 12b-12c: Alternative Sorting Metrics
# [KEEP ALL YOUR EXISTING ALTERNATIVE SORTING CODE FROM CELLS 12b and 12c]
# Including: calculate_brownest_metrics, calculate_mari_sorted_metrics, 
# calculate_pri_sorted_metrics, calculate_cci_sorted_metrics,
# calculate_phenology_metrics, calculate_cross_index_metrics,
# calculate_greenup_sorted_metrics, calculate_senescence_sorted_metrics,
# calculate_peak_sorted_metrics, calculate_dormancy_sorted_metrics,
# calculate_seasonal_range_metrics, calculate_all_alternative_metrics

# %% Cell 12b: Alternative Sorting Metrics (FIXED NaN handling)

def _get_nth_sorted_value(data_cube: np.ndarray, sort_cube: np.ndarray, 
                          n: int, ascending: bool = True) -> np.ndarray:
    """
    Get the nth value from data_cube after sorting by sort_cube.
    Properly handles NaN values by skipping them.

    Args:
        data_cube: The cube to extract values from
        sort_cube: The cube to sort by (e.g., NDVI)
        n: Position to extract (0 = first/lowest, -1 = last/highest)
        ascending: Sort order

    Returns:
        2D array of values at the nth valid position
    """
    n_time, h, w = data_cube.shape

    # Count valid observations per pixel
    valid_count = np.sum(np.isfinite(sort_cube), axis=0)

    # Sort with NaN handling
    if ascending:
        # NaN -> +inf so they sort to end
        sort_key = np.where(np.isfinite(sort_cube), sort_cube, np.inf)
    else:
        # NaN -> -inf so they sort to end (when reversed)
        sort_key = np.where(np.isfinite(sort_cube), sort_cube, -np.inf)

    sort_idx = np.argsort(sort_key, axis=0)
    if not ascending:
        sort_idx = sort_idx[::-1, :, :]

    sorted_data = np.take_along_axis(data_cube, sort_idx, axis=0)

    # Handle n
    if n >= 0:
        # nth from start
        result = sorted_data[n, :, :]
        # But this might be NaN if there weren't enough valid values
        # Mask where valid_count <= n
        result = np.where(valid_count > n, result, np.nan)
    else:
        # nth from end (e.g., -1 = last valid)
        # Need to index by valid_count + n
        idx = np.clip(valid_count + n, 0, n_time - 1).astype(int)
        i_idx = np.arange(h)[:, np.newaxis]
        j_idx = np.arange(w)[np.newaxis, :]
        result = sorted_data[idx, i_idx, j_idx]
        # Mask where not enough valid values
        result = np.where(valid_count >= abs(n), result, np.nan)

    return result

def calculate_brownest_metrics(index_cubes: Dict[str, np.ndarray], 
                                ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate brownest-sorted metrics.
    FIXED: Proper NaN handling for Brownest (single value) metrics.
    """
    metrics = {}

    for idx_name, idx_cube in index_cubes.items():
        sorted_brown = sort_by_ndvi(idx_cube, ndvi_cube, ascending=True)

        # Brownest3Mean uses metric_mean_n which is already fixed
        metrics[f'PACEIndex-{idx_name}-Brownest3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, ndvi_cube, 3, highest=False))

        # FIXED: Brownest single value
        # sort_by_ndvi puts NaN NDVI pixels at position 0 (VERY_LOW_SORT_VALUE)
        # So sorted_brown[0] may be from a NaN NDVI pixel
        # Solution: Use nanmin of the bottom 3 as approximation, or find first valid
        # Better: get the value at the lowest valid NDVI

        # Count valid NDVI per pixel location
        valid_ndvi_count = np.sum(np.isfinite(ndvi_cube), axis=0)

        # For pixels with valid data, brownest is the first valid after sorting
        # Since sort_by_ndvi uses VERY_LOW_SORT_VALUE for NaN, they go to front
        # So we need to skip over the NaN positions

        # Simple robust approach: take nanmean of bottom 1 (which handles the NaN)
        # Or use a dedicated function
        brownest_val = _get_nth_sorted_value(idx_cube, ndvi_cube, n=0, ascending=True)
        metrics[f'PACEIndex-{idx_name}-Brownest'] = scale_idx_named(idx_name, brownest_val)

    sorted_ndvi = sort_by_ndvi(ndvi_cube, ndvi_cube, ascending=True)
    metrics['NDVI-Brownest3Mean'] = scale_ndvi(metric_mean_n(sorted_ndvi, 3, from_top=False))

    # FIXED: NDVI Brownest
    brownest_ndvi = _get_nth_sorted_value(ndvi_cube, ndvi_cube, n=0, ascending=True)
    metrics['NDVI-Brownest'] = scale_ndvi(brownest_ndvi)

    return metrics





def calculate_mari_sorted_metrics(index_cubes: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Calculate mARI-sorted metrics. FIXED NaN handling."""
    metrics = {}

    if 'mARI' not in index_cubes:
        return metrics

    mari_cube = index_cubes['mARI']

    for idx_name, idx_cube in index_cubes.items():
        sorted_high_mari = sort_by_index(idx_cube, mari_cube, ascending=False)

        metrics[f'PACEIndex-{idx_name}-HighAnthocyanin3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, mari_cube, 3, highest=True))
        metrics[f'PACEIndex-{idx_name}-LowAnthocyanin3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, mari_cube, 3, highest=False))

        # FIXED: AmpAnthocyanin using nanmax/nanmin instead of sorted endpoints
        # v4: index at the highest-key composite minus index at the lowest-key one
        metrics[f'PACEIndex-{idx_name}-AmpAnthocyanin'] = scale_idx_named(idx_name, amplitude_by_key(idx_cube, mari_cube))

    return metrics


def calculate_pri_sorted_metrics(index_cubes: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Calculate PRI-sorted metrics. FIXED NaN handling."""
    metrics = {}

    if 'PRI' not in index_cubes:
        return metrics

    pri_cube = index_cubes['PRI']

    for idx_name, idx_cube in index_cubes.items():
        sorted_by_pri = sort_by_index(idx_cube, pri_cube, ascending=False)

        metrics[f'PACEIndex-{idx_name}-LeastStressed3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, pri_cube, 3, highest=True))
        metrics[f'PACEIndex-{idx_name}-MostStressed3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, pri_cube, 3, highest=False))

        # FIXED: AmpStress using nanmax/nanmin
        # v4: index at the highest-key composite minus index at the lowest-key one
        metrics[f'PACEIndex-{idx_name}-AmpStress'] = scale_idx_named(idx_name, amplitude_by_key(idx_cube, pri_cube))

    return metrics


def calculate_cci_sorted_metrics(index_cubes: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Calculate CCI-sorted metrics. FIXED NaN handling."""
    metrics = {}

    if 'CCI' not in index_cubes:
        return metrics

    cci_cube = index_cubes['CCI']

    for idx_name, idx_cube in index_cubes.items():
        sorted_by_cci = sort_by_index(idx_cube, cci_cube, ascending=False)

        metrics[f'PACEIndex-{idx_name}-HighChlorophyll3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, cci_cube, 3, highest=True))
        metrics[f'PACEIndex-{idx_name}-HighCarotenoid3Mean'] = scale_idx_named(idx_name, mean_at_extreme(idx_cube, cci_cube, 3, highest=False))

        # FIXED: AmpPigmentRatio using nanmax/nanmin
        # v4: index at the highest-key composite minus index at the lowest-key one
        metrics[f'PACEIndex-{idx_name}-AmpPigmentRatio'] = scale_idx_named(idx_name, amplitude_by_key(idx_cube, cci_cube))

    return metrics


def calculate_phenology_metrics(ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate phenology metrics."""
    metrics = {}

    with np.errstate(all='ignore'):
        ndvi_diff = np.diff(ndvi_cube, axis=0)

        max_greenup = np.nanmax(ndvi_diff, axis=0)
        metrics['Phenology-MaxGreenupRate'] = scale_ndvi(max_greenup)

        max_senescence = np.nanmin(ndvi_diff, axis=0)
        metrics['Phenology-MaxSenescenceRate'] = scale_ndvi(max_senescence)

        ndvi_for_argmax = np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube)
        metrics['Phenology-TimeToPeak'] = np.argmax(ndvi_for_argmax, axis=0).astype(np.int16)

        ndvi_for_argmin = np.where(np.isnan(ndvi_cube), np.inf, ndvi_cube)
        metrics['Phenology-TimeToMin'] = np.argmin(ndvi_for_argmin, axis=0).astype(np.int16)

        asymmetry = max_greenup + max_senescence
        metrics['Phenology-SeasonalAsymmetry'] = scale_ndvi(asymmetry)

        for thresh in [0.2, 0.3, 0.4, 0.5]:
            count = np.sum(ndvi_cube > thresh, axis=0)
            metrics[f'Phenology-GSL-gt-{int(thresh*10):02d}'] = count.astype(np.int16)

        ndvi_max = np.nanmax(ndvi_cube, axis=0)
        for frac in [0.50, 0.75]:
            threshold = ndvi_max * frac
            count = np.sum(ndvi_cube > threshold[np.newaxis, :, :], axis=0)
            metrics[f'Phenology-GSL-FracMax-{int(frac*100)}'] = count.astype(np.int16)

        integrated = np.nanmean(ndvi_cube, axis=0)
        metrics['Phenology-IntegratedNDVI'] = scale_ndvi(integrated)

        median_ndvi = np.nanmedian(ndvi_cube, axis=0)
        above_median = np.sum(ndvi_cube > median_ndvi[np.newaxis, :, :], axis=0)
        metrics['Phenology-GrowingSeasonLength'] = above_median.astype(np.int16)

    return metrics


def calculate_cross_index_metrics(index_cubes: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Calculate cross-index relationship metrics."""
    metrics = {}

    with np.errstate(all='ignore'):
        if 'MTCI' in index_cubes and 'EVI' in index_cubes:
            mtci_max = metric_max(index_cubes['MTCI'])
            evi_max = metric_max(index_cubes['EVI'])
            ratio = mtci_max / (evi_max + 0.001)
            ratio = np.where(np.isfinite(ratio), ratio, np.nan)
            metrics['CrossIndex-MTCI-EVI-Ratio'] = scale_index(ratio)

        for idx_name in ['PRI', 'mARI', 'CCI', 'NDWI', 'EVI']:
            if idx_name in index_cubes:
                idx_cube = index_cubes[idx_name]
                idx_range = metric_max(idx_cube) - metric_min(idx_cube)
                metrics[f'CrossIndex-{idx_name}-SeasonalRange'] = scale_idx_named(idx_name, idx_range)

        if 'NDWI' in index_cubes:
            metrics['CrossIndex-NDWI-DrySeason'] = scale_index(metric_min(index_cubes['NDWI']))
            metrics['CrossIndex-NDWI-WetSeason'] = scale_index(metric_max(index_cubes['NDWI']))

        if 'PRI' in index_cubes and 'mARI' in index_cubes:
            pri_cube = index_cubes['PRI']
            mari_cube = index_cubes['mARI']
            mari_sorted_by_pri = sort_by_index(mari_cube, pri_cube, ascending=True)
            metrics['CrossIndex-mARI-DuringStress'] = scale_index(mean_at_extreme(mari_cube, pri_cube, 3, highest=False))

    return metrics


def calculate_greenup_sorted_metrics(index_cubes: Dict[str, np.ndarray],
                                      ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate metrics at green-up transition."""
    metrics = {}

    with np.errstate(all='ignore'):
        ndvi_diff = np.diff(ndvi_cube, axis=0)
        ndvi_diff_masked = np.where(np.isnan(ndvi_diff), -np.inf, ndvi_diff)
        greenup_idx = np.argmax(ndvi_diff_masked, axis=0)

        greenup_rate = np.nanmax(ndvi_diff, axis=0)
        metrics['Phenology-GreenUpRate'] = scale_ndvi(greenup_rate)

        H, W = ndvi_cube.shape[1], ndvi_cube.shape[2]
        i_idx = np.arange(H)[:, np.newaxis]
        j_idx = np.arange(W)[np.newaxis, :]

        for idx_name, idx_cube in index_cubes.items():
            greenup_composite_idx = np.clip(greenup_idx + 1, 0, idx_cube.shape[0] - 1)
            value_at_greenup = idx_cube[greenup_composite_idx, i_idx, j_idx]
            metrics[f'PACEIndex-{idx_name}-AtGreenUp'] = scale_idx_named(idx_name, value_at_greenup)

        greenup_composite_idx = np.clip(greenup_idx + 1, 0, ndvi_cube.shape[0] - 1)
        ndvi_at_greenup = ndvi_cube[greenup_composite_idx, i_idx, j_idx]
        metrics['NDVI-AtGreenUp'] = scale_ndvi(ndvi_at_greenup)

        ndvi_before_greenup = ndvi_cube[greenup_idx, i_idx, j_idx]
        metrics['NDVI-BeforeGreenUp'] = scale_ndvi(ndvi_before_greenup)

    return metrics


def calculate_senescence_sorted_metrics(index_cubes: Dict[str, np.ndarray],
                                         ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate metrics at senescence transition."""
    metrics = {}

    with np.errstate(all='ignore'):
        ndvi_diff = np.diff(ndvi_cube, axis=0)
        ndvi_diff_masked = np.where(np.isnan(ndvi_diff), np.inf, ndvi_diff)
        senescence_idx = np.argmin(ndvi_diff_masked, axis=0)

        senescence_rate = np.abs(np.nanmin(ndvi_diff, axis=0))
        metrics['Phenology-SenescenceRate'] = scale_ndvi(senescence_rate)

        H, W = ndvi_cube.shape[1], ndvi_cube.shape[2]
        i_idx = np.arange(H)[:, np.newaxis]
        j_idx = np.arange(W)[np.newaxis, :]

        for idx_name, idx_cube in index_cubes.items():
            value_before_senescence = idx_cube[senescence_idx, i_idx, j_idx]
            metrics[f'PACEIndex-{idx_name}-BeforeSenescence'] = scale_idx_named(idx_name, value_before_senescence)

            senescence_after_idx = np.minimum(senescence_idx + 1, idx_cube.shape[0] - 1)
            value_after_senescence = idx_cube[senescence_after_idx, i_idx, j_idx]
            metrics[f'PACEIndex-{idx_name}-AfterSenescence'] = scale_idx_named(idx_name, value_after_senescence)

            senescence_change = value_after_senescence - value_before_senescence
            metrics[f'PACEIndex-{idx_name}-SenescenceChange'] = scale_idx_named(idx_name, senescence_change)

        metrics['NDVI-BeforeSenescence'] = scale_ndvi(ndvi_cube[senescence_idx, i_idx, j_idx])
        senescence_after_idx = np.minimum(senescence_idx + 1, ndvi_cube.shape[0] - 1)
        metrics['NDVI-AfterSenescence'] = scale_ndvi(ndvi_cube[senescence_after_idx, i_idx, j_idx])

    return metrics


def calculate_peak_sorted_metrics(index_cubes: Dict[str, np.ndarray],
                                   ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate metrics at peak NDVI."""
    metrics = {}

    with np.errstate(all='ignore'):
        ndvi_masked = np.where(np.isnan(ndvi_cube), -np.inf, ndvi_cube)
        peak_ndvi_idx = np.argmax(ndvi_masked, axis=0)

        H, W = ndvi_cube.shape[1], ndvi_cube.shape[2]
        i_idx = np.arange(H)[:, np.newaxis]
        j_idx = np.arange(W)[np.newaxis, :]

        for idx_name, idx_cube in index_cubes.items():
            value_at_peak = idx_cube[peak_ndvi_idx, i_idx, j_idx]
            metrics[f'PACEIndex-{idx_name}-AtPeakNDVI'] = scale_idx_named(idx_name, value_at_peak)

    return metrics


def calculate_dormancy_sorted_metrics(index_cubes: Dict[str, np.ndarray],
                                       ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate metrics at minimum NDVI (dormancy)."""
    metrics = {}

    with np.errstate(all='ignore'):
        ndvi_masked = np.where(np.isnan(ndvi_cube), np.inf, ndvi_cube)
        min_ndvi_idx = np.argmin(ndvi_masked, axis=0)

        H, W = ndvi_cube.shape[1], ndvi_cube.shape[2]
        i_idx = np.arange(H)[:, np.newaxis]
        j_idx = np.arange(W)[np.newaxis, :]

        for idx_name, idx_cube in index_cubes.items():
            value_at_min = idx_cube[min_ndvi_idx, i_idx, j_idx]
            metrics[f'PACEIndex-{idx_name}-AtMinNDVI'] = scale_idx_named(idx_name, value_at_min)

    return metrics


def calculate_seasonal_range_metrics(index_cubes: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Calculate seasonal range for each index."""
    metrics = {}

    with np.errstate(all='ignore'):
        for idx_name, idx_cube in index_cubes.items():
            idx_max = np.nanmax(idx_cube, axis=0)
            idx_min = np.nanmin(idx_cube, axis=0)
            seasonal_range = idx_max - idx_min
            metrics[f'PACEIndex-{idx_name}-SeasonalRange'] = scale_idx_named(idx_name, seasonal_range)

    return metrics


def calculate_all_alternative_metrics(index_cubes: Dict[str, np.ndarray],
                                       ndvi_cube: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate all alternative sorting metrics."""
    metrics = {}

    logger.info("  Calculating brownest-sorted metrics...")
    metrics.update(calculate_brownest_metrics(index_cubes, ndvi_cube))

    logger.info("  Calculating mARI-sorted metrics...")
    metrics.update(calculate_mari_sorted_metrics(index_cubes))

    logger.info("  Calculating PRI-sorted metrics...")
    metrics.update(calculate_pri_sorted_metrics(index_cubes))

    logger.info("  Calculating CCI-sorted metrics...")
    metrics.update(calculate_cci_sorted_metrics(index_cubes))

    logger.info("  Calculating phenology metrics...")
    metrics.update(calculate_phenology_metrics(ndvi_cube))

    logger.info("  Calculating green-up sorted metrics...")
    metrics.update(calculate_greenup_sorted_metrics(index_cubes, ndvi_cube))

    logger.info("  Calculating senescence sorted metrics...")
    metrics.update(calculate_senescence_sorted_metrics(index_cubes, ndvi_cube))

    logger.info("  Calculating peak-NDVI sorted metrics...")
    metrics.update(calculate_peak_sorted_metrics(index_cubes, ndvi_cube))

    logger.info("  Calculating dormancy sorted metrics...")
    metrics.update(calculate_dormancy_sorted_metrics(index_cubes, ndvi_cube))

    logger.info("  Calculating seasonal range metrics...")
    metrics.update(calculate_seasonal_range_metrics(index_cubes))

    logger.info("  Calculating cross-index metrics...")
    metrics.update(calculate_cross_index_metrics(index_cubes))

    return metrics


print("Alternative sorting metrics defined (FIXED NaN handling)")

# %% Cell 13: GeoTIFF Writing
def get_tile_geotransform(tile: str) -> tuple:
    """Get GDAL geotransform for a MODIS tile at 2km resolution."""
    MODIS_UPPER_LEFT_X = -20015109.354
    MODIS_UPPER_LEFT_Y = 10007554.677
    MODIS_TILE_SIZE_M = 1111950.5196666666

    h = int(tile[1:3])
    v = int(tile[4:6])

    min_x = MODIS_UPPER_LEFT_X + h * MODIS_TILE_SIZE_M
    max_y = MODIS_UPPER_LEFT_Y - v * MODIS_TILE_SIZE_M
    pixel_size = MODIS_TILE_SIZE_M / TILE_SIZE

    return (min_x, pixel_size, 0, max_y, 0, -pixel_size)


def get_sinusoidal_srs() -> osr.SpatialReference:
    """Get MODIS sinusoidal spatial reference."""
    srs = osr.SpatialReference()
    srs.ImportFromProj4('+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs')
    return srs


def write_metrics_geotiff(metrics: Dict[str, np.ndarray], output_path: Path, 
                          tile: str, metric_prefix: str):
    """Write metrics to a multi-band GeoTIFF."""
    band_names = sorted(metrics.keys())
    n_bands = len(band_names)

    if n_bands == 0:
        logger.warning(f"No metrics to write for {metric_prefix}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(
        str(output_path),
        TILE_SIZE, TILE_SIZE, n_bands,
        gdal.GDT_Int16,
        options=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=YES']
    )

    ds.SetGeoTransform(get_tile_geotransform(tile))
    ds.SetProjection(get_sinusoidal_srs().ExportToWkt())

    for i, band_name in enumerate(band_names):
        band = ds.GetRasterBand(i + 1)
        band.WriteArray(metrics[band_name])
        band.SetNoDataValue(NO_DATA_INT)
        band.SetDescription(band_name)

    ds.FlushCache()
    ds = None

    logger.info(f"  Wrote {output_path.name}: {n_bands} bands (Int16)")


print("GeoTIFF writing functions defined")


# %% Cell 13b: Bands not written in v4
# Each of these is the same quantity as the band named on its right, so it adds
# nothing. Measured 2026-10-12: byte-identical on 40 training chips from 40
# tiles (duplicate_band_groups_521.json), or the same definition differing in
# <=0.02% of pixels on 3 full tiles. The band on the right is kept.
_INDEX_NAMES = ['EVI', 'NDWI', 'PRI', 'CIRE', 'NDRE', 'GCI', 'MTCI', 'CCI', 'mARI', 'NDII', 'REP', 'REIP']
DROPPED_BANDS_V4 = {
    # NDVI sorted by NDVI is just NDVI's own statistic
    'BandReflMaxGreenness-NDVI': 'BandReflMax-NDVI',
    'BandReflMinGreenness-NDVI': 'BandReflMin-NDVI',
    'BandReflMedianGreenness-NDVI': 'BandReflMedian-NDVI',
    'AmpGreenestBandRefl-NDVI': 'AmpBandRefl-NDVI',
    'NDVI-Brownest': 'BandReflMin-NDVI',
    # an index sorted by itself: highest minus lowest is its plain amplitude
    'PACEIndex-mARI-AmpAnthocyanin': 'PACEIndex-mARI-Amp',
    'PACEIndex-PRI-AmpStress': 'PACEIndex-PRI-Amp',
    'PACEIndex-CCI-AmpPigmentRatio': 'PACEIndex-CCI-Amp',
    # an index at its own 3 highest values is its -Highest3Mean
    'PACEIndex-CCI-HighChlorophyll3Mean': 'PACEIndex-CCI-Highest3Mean',
    'PACEIndex-PRI-LeastStressed3Mean': 'PACEIndex-PRI-Highest3Mean',
    'PACEIndex-mARI-HighAnthocyanin3Mean': 'PACEIndex-mARI-Highest3Mean',
    # thermal band at the 3 greenest / 3 warmest composites: keep the MODIS C6 names
    'Greenest3MeanBandRefl-Band31': 'TempMeanGreenest3',
    'Warmest3MeanBandRefl-Band31': 'TempMeanWarmest3',
    # same statistic under a second name
    'CrossIndex-NDWI-WetSeason': 'PACEIndex-NDWI-Max',
    'CrossIndex-NDWI-DrySeason': 'PACEIndex-NDWI-Min',
    'CrossIndex-mARI-DuringStress': 'PACEIndex-mARI-MostStressed3Mean',
    'Phenology-MaxGreenupRate': 'Phenology-GreenUpRate',
}
# max - min of the index under two more names
DROPPED_BANDS_V4.update({f'PACEIndex-{i}-SeasonalRange': f'PACEIndex-{i}-Amp' for i in _INDEX_NAMES})
DROPPED_BANDS_V4.update({f'CrossIndex-{i}-SeasonalRange': f'PACEIndex-{i}-Amp' for i in ['PRI', 'mARI', 'CCI', 'NDWI', 'EVI']})
# index at the single lowest-NDVI composite, under a second name
DROPPED_BANDS_V4.update({f'PACEIndex-{i}-Brownest': f'PACEIndex-{i}-AtMinNDVI' for i in _INDEX_NAMES})


def drop_duplicate_bands(metrics: Dict[str, np.ndarray], group: str, seen: set) -> Dict[str, np.ndarray]:
    """Remove this file's DROPPED_BANDS_V4 entries; record them in `seen`."""
    dropped = [name for name in metrics if name in DROPPED_BANDS_V4]
    seen.update(dropped)
    logger.info(f"  {group}: not writing {len(dropped)} duplicate bands")
    return {name: arr for name, arr in metrics.items() if name not in DROPPED_BANDS_V4}


def check_dropped_bands(seen: set, written: set) -> None:
    """Fail loudly if the drop list has gone stale: every dropped band must have
    been produced, and the band it duplicates must have been written."""
    never_produced = sorted(set(DROPPED_BANDS_V4) - seen)
    keeper_missing = sorted({k for k in DROPPED_BANDS_V4.values() if k not in written})
    if never_produced or keeper_missing:
        raise RuntimeError(f"DROPPED_BANDS_V4 is stale: never produced {never_produced}; "
                           f"kept band missing {keeper_missing}")


# %% Cell 14: Main Processing Function (UPDATED)
def process_tile_metrics(tile: str):
    """Process all metrics for a single tile."""

    print(f"\n{'='*60}")
    print(f"PROCESSING METRICS: {tile}")
    print(f"{'='*60}")

    composite_dir = OUTPUT_BASE / tile / str(YEAR) / "2-Composites"
    metrics_dir = METRICS_OUT_BASE / tile / str(YEAR) / METRICS_SUBDIR
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # Load bands
    logger.info("Loading band data...")
    bands = load_all_bands(composite_dir, tile)

    # Calculate NDVI
    logger.info("Calculating NDVI...")
    ndvi_cube = get_ndvi_cube(bands)
    thermal_cube = bands[BAND_THERMAL]

    # =========================================================================
    # MODIS-Compatible Metrics (UPDATED with Band31, snow, QA)
    # =========================================================================
    logger.info("Calculating MODIS-compatible metrics...")

    modis_metrics = {}

    # Basic metrics for reflectance bands
    modis_metrics.update(calculate_basic_metrics(bands, ndvi_cube))
    modis_metrics.update(calculate_lowest_n_metrics(bands))
    modis_metrics.update(calculate_greenness_metrics(bands, ndvi_cube))
    modis_metrics.update(calculate_thermal_sorted_metrics(bands, ndvi_cube, thermal_cube))
    modis_metrics.update(calculate_unsorted_monthly(bands, ndvi_cube))

    # NEW: Band31 (thermal) basic metrics
    modis_metrics.update(calculate_band31_basic_metrics(thermal_cube, ndvi_cube))

    # NEW: Snow detection and snow-free metrics
    # NEW:
    snow_metrics, snow_mask = calculate_snow_metrics(
        bands['Band_3'], bands['Band_4'], bands['Band_7'], ndvi_cube, thermal_cube
    )
    modis_metrics.update(snow_metrics)

    # NEW: QA observation count metrics (diagnostic only)
    modis_metrics.update(calculate_qa_observation_metrics(bands, thermal_cube))

    dropped_seen = set()
    modis_metrics = drop_duplicate_bands(modis_metrics, "MODIS", dropped_seen)
    write_metrics_geotiff(modis_metrics, metrics_dir / "MODIS_Metrics.tif", tile, "MODIS")

    # =========================================================================
    # PACE-Enhanced Metrics
    # =========================================================================
    logger.info("Calculating PACE-enhanced metrics...")
    pace_metrics, index_cubes = calculate_pace_indices(composite_dir, tile, ndvi_cube)
    pace_metrics = drop_duplicate_bands(pace_metrics, "PACE", dropped_seen)
    write_metrics_geotiff(pace_metrics, metrics_dir / "PACE_Metrics.tif", tile, "PACE")

    # =========================================================================
    # Alternative Sorting Metrics
    # =========================================================================
    logger.info("Calculating alternative sorting metrics...")
    alt_metrics = calculate_all_alternative_metrics(index_cubes, ndvi_cube)
    alt_metrics = drop_duplicate_bands(alt_metrics, "AltSort", dropped_seen)
    check_dropped_bands(dropped_seen, set(modis_metrics) | set(pace_metrics) | set(alt_metrics))
    write_metrics_geotiff(alt_metrics, metrics_dir / "PACE_AltSort_Metrics.tif", tile, "AltSort")

    # Summary
    total_metrics = len(modis_metrics) + len(pace_metrics) + len(alt_metrics)
    print(f"\n  MODIS metrics:   {len(modis_metrics)} (includes Band31, snow, QA)")
    print(f"  PACE metrics:    {len(pace_metrics)}")
    print(f"  AltSort metrics: {len(alt_metrics)}")
    print(f"  Total:           {total_metrics}")
    print(f"\n✓ Completed {tile}")

    return len(modis_metrics), len(pace_metrics), len(alt_metrics)


# =============================================================================
# CLI entry point (added for batch/SLURM use -- not part of the original
# notebook). Runs metrics generation for ONE tile, with resumability: skips
# the tile entirely if all three expected output GeoTIFFs already exist and
# are readable, unless --force is passed.
# =============================================================================

def _metrics_outputs_complete(tile: str) -> bool:
    """True if this tile's 3-Metrics GeoTIFFs already exist and are openable."""
    metrics_dir = METRICS_OUT_BASE / tile / str(YEAR) / METRICS_SUBDIR
    # v4 band counts (v4_band_list.json). A file with a different count is from
    # an interrupted or older run and is redone.
    expected = {"MODIS_Metrics.tif": 298, "PACE_Metrics.tif": 146, "PACE_AltSort_Metrics.tif": 206}
    for name, n_bands in expected.items():
        path = metrics_dir / name
        if not path.exists():
            return False
        try:
            ds = gdal.Open(str(path))
            if ds is None or ds.RasterCount != n_bands:
                return False
            ds = None
        except Exception:
            return False
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate PACE-VCF metrics v4 for one tile.")
    parser.add_argument("--tile", required=True, help="Tile id, e.g. h12v04")
    parser.add_argument("--force", action="store_true",
                         help="Reprocess even if output already exists")
    args = parser.parse_args()

    if not args.force and _metrics_outputs_complete(args.tile):
        logger.info(f"{args.tile}: metrics already complete, skipping (use --force to redo)")
        raise SystemExit(0)

    composite_dir = OUTPUT_BASE / args.tile / str(YEAR) / "2-Composites"
    if not composite_dir.exists():
        logger.error(f"{args.tile}: no composites found at {composite_dir} -- run "
                      f"composite generation first")
        raise SystemExit(1)

    process_tile_metrics(args.tile)
