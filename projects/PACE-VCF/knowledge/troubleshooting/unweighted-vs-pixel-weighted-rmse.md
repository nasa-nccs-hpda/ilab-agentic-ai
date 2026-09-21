# Troubleshooting: a headline RMSE number was inflated by ~1.5 points from naive averaging

## Symptom

Not a crash -- a plausible-looking but misleading result. An AlphaEarth
fine-resolution regression model (see
`knowledge/models/super-resolution-2km-to-250m.md`) was evaluated per-tile
across 23 test tiles, then summarized as:

```python
overall_rmse = float(np.mean([m["rmse"] for m in results]))
```

giving a headline "Mean RMSE: 7.36%". Looked strong. Looking at the
per-tile table used to compute it, one tile had `n_valid=1,054` (a few
thousand pixels) sitting in the same unweighted average as tiles with
`n_valid` over 20 million -- and that same tiny tile had
`correlation_r2=0.0000`, a hallmark of a near-constant target with too few
samples for a meaningful correlation.

## Confirmed cause

`np.mean()` over a list of per-tile RMSE values weights every tile
**equally**, regardless of how many pixels each tile actually contributed.
Per-tile sample sizes here ranged from 1,054 to ~23,000,000 -- a
~20,000x spread. Several of the worst-performing tiles (RMSE 17.13%,
13.12%, 12.15%, 10.93%) also happened to be among the largest by pixel
count (19-23 million each), so they were *under*-represented in the simple
average relative to how much land area they actually cover, while some
small-sample tiles pulled the average down (or, in the degenerate `n=1,054`
case, contributed a number that isn't really measuring anything).

## Resolution

Computed a pixel-weighted ("pooled") RMSE instead -- the mathematically
correct way to combine per-tile RMSEs, since `RMSE_i^2 * n_i` recovers each
tile's total squared error:

```python
total_sq_error = sum(m["rmse"] ** 2 * m["n_valid"] for m in results)
total_n = sum(m["n_valid"] for m in results)
pooled_rmse = (total_sq_error / total_n) ** 0.5
```

This moved the headline number from 7.36% to roughly **8.8-8.9%** -- still
a real improvement over the comparison baseline, but a meaningfully smaller
one than the naive average implied. It also naturally solves the
degenerate-tiny-tile problem without needing a manual exclusion rule: a
tile with `n=1,054` contributes essentially nothing to a sum dominated by
tiles with tens of millions of pixels, whereas it counted as a full,
equal-weight data point in the plain average.

## General lesson

Never average a per-group metric (RMSE, accuracy, error rate) across groups
of wildly different size without checking whether the metric needs to be
pooled/weighted instead. This is especially easy to miss for RMSE
specifically, because `RMSE_i^2` (not `RMSE_i` itself) is the quantity that
's proportional to total squared error and therefore the right thing to
weight by sample count -- naively weighting the RMSE values themselves
(rather than their squares) would still be wrong. Before reporting a
"mean" of any per-tile/per-group metric, check the sample-size spread
across groups; if it's large, pool rather than average.
