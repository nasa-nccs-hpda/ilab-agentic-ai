# Model: XGBoost + Monte Carlo feature selection

The primary model family for this project. Two variants exist (tabular
"legacy" and image "chips" -- see `knowledge/overview/project-overview.md`),
each with and without AlphaEarth features, but they share this training
methodology.

## Why Monte Carlo feature selection

With 500+ candidate features (MODIS-equivalent + PACE hyperspectral +
AltSort phenology-sorted + optionally AlphaEarth), the full-feature model is
accurate but expensive and hard to interpret. Monte Carlo feature selection
trains many small models on random feature subsets and keeps the features
that consistently prove useful, producing a much smaller, nearly as
accurate, more interpretable model.

```python
N_TRIALS = 100
FEATURES_PER_TRIAL = 50
MIN_FEATURE_USAGE = 10
TOP_N_FEATURES = 50   # increased from an earlier 30 for better coverage
```

Each trial trains a small XGBoost model on a random 50-feature subset and
scores it; a feature's average importance across all trials it appeared in,
plus how many trials used it, determines whether it makes the final top-N
list.

## Train/validation/test split

**Current, correct methodology (all four training notebooks, as of the last
fix):** a 70/15/15 split. Train fits every model. Validation scores every
Monte Carlo trial and therefore drives feature selection. Test is touched
only once, for the final reported number.

This matters because an earlier version of two of the four training
notebooks (the "legacy" family) used only a train/test split (80/20) and
reused the *same* test set both to score all 100 Monte Carlo trials (i.e.
to decide which features are "top") and to report the final model's R².
Because the test set indirectly shaped which features got selected, its
final "test R²" was not a clean holdout -- a form of feature-selection
leakage that mildly overstates performance. This was found and fixed;
see `knowledge/troubleshooting/test-set-leakage-in-monte-carlo-selection.md`.

## Balanced sampling

Tree-cover ground truth is heavily imbalanced toward bare/low-vegetation
pixels globally. Training samples are re-balanced before the split:

```python
TARGET_BARE_PCT = 0.25       # 0% tree cover
TARGET_LOW_PCT = 0.25        # 1-25%
TARGET_FOREST_PCT = 0.08     # 81-100%, upsampled (with replacement) if needed
# Medium (26-50%) and High (51-80%) kept as-is
```

## XGBoost hyperparameters

```python
XGB_PARAMS = {
    'tree_method': 'gpu_hist',
    'n_estimators': 500,
    'max_depth': 10,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'missing': np.nan,   # native NaN handling, no median imputation
}
```

Monte Carlo trial models use a faster/shallower variant
(`n_estimators=100, max_depth=8`) since only relative feature importance
matters at that stage, not final accuracy.

## Feature exclusions

- QA metrics (diagnostic-only columns, e.g. `QA_*`) are excluded from
  training -- including them would leak information not available at true
  inference time.
- `UnsortedMonthly` (calendar-based) metrics are excluded by default
  (`INCLUDE_UNSORTED = False`) -- see
  `knowledge/algorithms/altsort-phenology-metrics.md` for why.

## Reported performance (tabular/legacy, MODIS + PACE, post-fix)

| Model | R² (squared Pearson) | RMSE | Features |
| --- | --- | --- | --- |
| Full model | ~0.80 | ~13% | 519 |
| Monte Carlo (top 50) | ~0.76 | ~14% | 50 |

Per-tile performance varies by biome (see `knowledge/datasets/modis-vcf-mod44b.md`
for the reasons). See `knowledge/algorithms/two-r2-definitions.md` before
comparing these numbers to results reported elsewhere in this project.
