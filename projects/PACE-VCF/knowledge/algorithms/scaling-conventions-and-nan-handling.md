# Algorithm: Int16 scaling conventions and NaN handling

## Storage convention

All metrics TIFs use `NO_DATA = -10001` and store values as Int16, scaled by
value type:

```python
def scale_reflectance(data):
    """Reflectance (0-1) -> Int16: multiply by 10,000."""
    scaled = data * 10000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_ndvi(data):
    """NDVI/indices (-1 to 1) -> Int16: multiply by 1,000."""
    scaled = data * 1000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_thermal(data):
    """Absolute temperature (Kelvin) -> Int16: multiply by 100."""
    scaled = data * 100
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)

def scale_index(data):
    """Generic index (-1 to 1) -> Int16: multiply by 1,000."""
    scaled = data * 1000
    return np.where(np.isfinite(scaled), scaled, NO_DATA).astype(np.int16)
```

**Important distinction, learned the hard way:** `scale_thermal()` gates
validity on `200 < data < 400` (i.e. it only accepts absolute Kelvin
values). Applying it to a *difference* of two temperatures (e.g. max-min, or
greenest-minus-brownest) makes every pixel fail that range check and become
NO_DATA -- silently, with no error. A separate `scale_thermal_diff()` (same
x100 scaling, no absolute-range gate) exists for exactly this case. This
distinction was lost and re-introduced across several notebook iterations --
see `knowledge/troubleshooting/scale-thermal-diff-regression.md`.

## NaN handling for thermal data gaps

VIIRS thermal coverage is frequently lower than PACE optical coverage for
the same pixel/composite (different orbits, cloud masking, QA filtering).
Three patterns are used depending on how the value is consumed:

**1. Sorted metrics (warmest/coolest):** replace NaN with ±infinity so it
sorts to the excluded end rather than being selected as an extreme value.
```python
thermal_for_warmest = np.where(np.isfinite(thermal_cube), thermal_cube, -np.inf)
thermal_for_coolest = np.where(np.isfinite(thermal_cube), thermal_cube, np.inf)
```

**2. Phenology-indexed values (e.g. thermal at peak NDVI):** fall back to the
per-pixel temporal mean if the specific indexed composite has no thermal
data.
```python
thermal_at_peak = thermal_cube[peak_ndvi_idx, i_idx, j_idx]
thermal_mean = np.nanmean(thermal_cube, axis=0)
thermal_at_peak = np.where(np.isfinite(thermal_at_peak), thermal_at_peak, thermal_mean)
```

**3. Snow metrics in no-snow regions:** if a region is snow-free
(`snow_pct < 1.0`), `SnowFree-*` metrics simply equal the regular metrics
(everything already is snow-free), rather than being computed from a
snow-conditional subset that might be empty.

**4. First-valid-value scanning** (used for e.g. `LST-AtFirstSnowFree`):
```python
def get_first_valid(cube):
    """Get first valid (non-NaN) value for each pixel across time."""
    H, W = cube.shape[1], cube.shape[2]
    result = np.full((H, W), np.nan, dtype=np.float32)
    for t in range(cube.shape[0]):
        needs_fill = np.isnan(result) & np.isfinite(cube[t, :, :])
        result = np.where(needs_fill, cube[t, :, :], result)
        if np.all(np.isfinite(result)):
            break
    result = np.where(np.isfinite(result), result, np.nanmean(cube, axis=0))
    return result
```

## Diagnostic: check metric validity

```python
with rasterio.open(metrics_path) as src:
    for i, name in enumerate(src.descriptions):
        data = src.read(i + 1)
        valid_pct = 100 * np.sum(data != -10001) / data.size
        if valid_pct < 99:
            print(f"{name}: {valid_pct:.1f}% valid")
```

Run this after generating or regenerating a metrics file -- it's the check
that would have caught the `scale_thermal`/`scale_thermal_diff` regression
immediately (two bands at a flat 0% valid, every tile, every time).
