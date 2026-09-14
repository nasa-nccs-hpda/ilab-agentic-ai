# Dataset: AlphaEarth Foundations satellite embeddings

## What it is

AlphaEarth Foundations Satellite Embedding V1 is a foundation-model
embedding product: 64-dimensional per-pixel embeddings at 10 m native
resolution, published as annual composites. This project uses it as an
additional feature source (Experiment 4), not as a training target.

- **Embedding year used:** 2020, fixed. AlphaEarth's annual composites don't
  yet reach this project's PACE processing year (2025), so 2020 is used as a
  static proxy layer -- a deliberate simplification, not "most recent
  available." Revisit if the project resumes and later years become
  available.
- **Aggregation to 2 km:** min/mean/median/max per embedding dimension,
  giving 256 bands (4 stats x 64 dims), stored Int16 x1000-scaled
  (`NO_DATA = -10001`), named e.g. `A00_min`...`A63_max`.

## Access: use direct GCS, not Earth Engine

**Do not use Earth Engine's compute API** (`reduceResolution` +
`Export.image.toAsset`) to aggregate AlphaEarth to 2 km -- it is structurally
infeasible for this use case; see
`knowledge/troubleshooting/earth-engine-pixel-ceiling-dead-end.md` for the
full failure chain (real effort was spent on this before the pivot, so it's
recorded to prevent repeating it).

The working approach reads AlphaEarth's raw Cloud-Optimized GeoTIFFs
directly from the public GCS bucket, with no Earth Engine account, OAuth, or
billing project required:

- **Bucket layout:**
  `gs://alphaearth_foundations/satellite_embedding/v1/annual/{year}/{utm_zone}/*.tiff`
  -- each file is 8192x8192 px, 64 channels, signed 8-bit integers,
  NoData = `-128`.
- **De-quantization** (exact formula -- do not reconstruct from memory, a
  plausible-looking wrong formula would silently corrupt data):
  ```python
  de_quantized_values = ((values / 127.5) ** 2) * np.sign(values)
  ```
  Mask out `-128` (NoData) *before* applying this formula.
- **No filename index.** The bucket's own `aef_index.csv`/`.parquet`/`.gpkg`
  gives bounds per file but not the file path. List the candidate
  `{year}/{utm_zone}/` prefix via the public JSON listing API, then open each
  candidate file's GDAL header (cheap) and check its real bounds -- slower
  than an index join, but correct by construction.
- **UTM zone matching:** a ~1112 km MODIS sinusoidal tile can span multiple
  6-degree UTM zones and, if it straddles the equator, both the `N` and `S`
  folder for each zone. Sample multiple points across the tile's bounding
  box, not just center/corners, to build the candidate zone set.
- **Aggregation:** true native-resolution (10 m) exhaustive aggregation
  across a full 2 km tile isn't memory-feasible locally either. The working
  approach uses `gdal.Warp()` (nearest-neighbor) onto a configurable
  sub-sample grid (default 8x8 = 64 samples per output cell, i.e. 250 m
  intermediate resolution), then block-reduces to the 2 km output. This is a
  documented, tunable fidelity/memory tradeoff, not an exact replication of
  what native-resolution aggregation would produce.

## Sanity check

Since min/mean/median/max are computed independently per embedding
dimension, a cheap validity check is `min <= mean/median <= max` (with small
tolerance for independent Int16 rounding) on a sample of valid pixels per
dimension -- this catches a broken de-quantization formula or a
reshape/reduction axis mixup. Run after any change to the aggregation logic.

## Result

AlphaEarth features are read into training the same way as the other metrics
files (prefixed `AlphaEarth_`, gated by an `INCLUDE_ALPHAEARTH` flag). In
feature-importance rankings, AlphaEarth dimensions appear but rank below the
hand-engineered PACE hyperspectral indices (REIP, CCI, etc.) -- they add
information rather than replacing domain-specific indices.

## Performance note

Extraction time depends heavily on how many UTM zones a tile spans. A
mid-latitude tile with few zones is fast; an equatorial tile straddling the
equator (e.g. `h12v09`, Amazon, 6 zones / ~2400 candidate files / 313
actually covering) took ~38 minutes for file discovery alone with sequential
header checks, reduced by parallelizing the per-file header check with a
24-worker thread pool (I/O-bound, so threading rather than multiprocessing is
appropriate -- each thread must build its own coordinate-transformation
objects rather than sharing them).
