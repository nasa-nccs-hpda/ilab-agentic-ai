# Troubleshooting: 0.1% missing data corrupted 99%+ of a guided-filter output

## Symptom

A plotted example of the guided-filter super-resolution output (see
`knowledge/models/super-resolution-2km-to-250m.md`) was blank/white across
almost the entire tile, with only a small sliver of real values in one
corner. Separately, roughly a third of guide tiles were being silently
dropped from the hyperparameter search entirely (`evaluate_holdout()`
returning `None` because it found zero valid held-out pixels), and the
plain-baseline RMSE was drifting inconsistently between rows of the search
results that should have been identical (baseline doesn't depend on the
guided filter's hyperparameters).

## Confirmed cause, quantified

Added a one-line diagnostic (`np.isnan(array).mean()`) at each stage of the
guided filter and got: **0.0975% NaN in the guide array -> 99.28% NaN in the
final output**, for one representative tile.

`scipy.ndimage.uniform_filter` (the box filter used throughout) is not
NaN-aware: if a single pixel in a filter window is NaN, the entire window's
output is NaN. The guided filter calls this box filter **twice in
sequence** (once for `mean_g`/`mean_t`/`mean_gt`/`mean_gg`, again for
`mean_a`/`mean_b`), so a single isolated NaN source pixel contaminates a
halo roughly `4 x radius` wide around itself, not just `radius`. Real
satellite NoData tends to scatter fairly evenly across a tile (sensor
artifacts, small QA-masked gaps) rather than cluster in one blob -- with
~22,000 scattered NaN pixels across a 4800x4800 tile (0.1%), the average
spacing between them was small enough relative to the contamination halo
that the halos overlapped almost everywhere, engulfing nearly the whole
tile. This is the standard "sparse points + wide dilation = near-total
coverage" effect from stochastic geometry, not a rare edge case.

`evaluate_holdout()` only scores pixels where `np.isfinite(sr_result)` --
so this wasn't just corrupting the visualization, it was silently reducing
the scored area of every affected tile to whatever tiny fraction of pixels
survived the cascade, and dropping entire tiles to zero scored pixels when
the contamination reached 100%.

## Resolution

Replaced the NaN-propagating box filter with a NaN-aware ("normalized
convolution") version: filter the data with NaNs replaced by 0 *and*
separately filter a binary valid/invalid mask, then divide one by the
other. A pixel only ends up NaN in the output if its *entire* window had
zero valid input (rare), not if a single pixel in the window was missing.

```python
def box_filter(img, radius):
    valid = np.isfinite(img).astype(np.float32)
    filled = np.where(valid.astype(bool), img, 0.0)
    size = 2 * radius + 1
    sum_vals = uniform_filter(filled, size=size, mode="reflect") * size ** 2
    sum_valid = uniform_filter(valid, size=size, mode="reflect") * size ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        result = sum_vals / sum_valid
    result[sum_valid == 0] = np.nan
    return result
```

After the fix, re-running the same diagnostic on the same tile gave
`NaN in sr_result == NaN in guide` exactly, for every tile checked --
confirming zero amplification, only genuinely-missing pixels stay missing.
This also resolved the previously-inconsistent baseline drift (it was
really a symptom of the guide-tile subset silently changing between search
rows, caused by different tiles hitting 100% contamination at different
hyperparameter settings) and recovered the ~30% of guide tiles and 4 of 23
test tiles (including both singleton Arctic regions) that had been dropped
from evaluation entirely.

## General lesson

`scipy.ndimage.uniform_filter` (and most plain box/Gaussian filters) treat
NaN as radioactive -- a tiny, even very sparse, amount of missing data can
silently spread to dominate the output once the filter is applied more than
once in sequence. If input data can have any NaN/NoData at all and a filter
result feeds into another filter, use a NaN-aware ("normalized
convolution") filter from the start rather than discovering the
contamination visually or through inconsistent downstream numbers.
