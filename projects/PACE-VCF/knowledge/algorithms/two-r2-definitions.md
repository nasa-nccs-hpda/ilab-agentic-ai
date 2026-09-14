# Algorithm note: two incompatible R² definitions in this project

This project's own code computes R² two different ways in different places.
Mixing them produces numbers that look comparable but aren't. Read this
before quoting or comparing any R² value from this project.

## The two definitions

1. **`coefficient_of_determination`** -- the conventional statistical R²,
   `1 - SS_res / SS_tot`. Penalizes systematic bias/offset: a model that's
   consistently too high by a constant amount scores worse here.
2. **`correlation_r2`** -- squared Pearson correlation coefficient,
   `pearsonr(y_true, y_pred) ** 2`. Measures only how well predictions track
   truth *linearly*; a model with a constant offset can still score highly
   here even though its predictions are biased.

Both are legitimate metrics; they answer different questions. The problem is
using them interchangeably without noting which one a given number is.

## Where each is used

- The legacy/tabular XGBoost training notebooks compute R² as squared
  Pearson correlation (`correlation_r2`) throughout -- with one exception
  that was found and fixed: the final Monte-Carlo-selected model's reported
  R² used the conventional `coefficient_of_determination` while every other
  reported number in the same notebook (full model, every MC trial) used
  squared Pearson. This inconsistency was corrected so the whole notebook
  now reports squared Pearson consistently.
- A colleague's separate model-comparison codebase (used for the
  Spatial-CNN and Pixel-Transformer models) computes both metrics per model
  run and exposes them under these exact two names, plus a third field
  (`pearson_r`, unsquared) -- but a third module in the same codebase reports
  the same `correlation_r2` quantity again under yet another name
  (`r2`) in a different output file, making it easy to accidentally
  treat two differently-named fields as different metrics when they're the
  same one.

## The choice made for this project's headline comparisons

The three-model comparison (XGBoost vs. Spatial-CNN vs. Pixel-Transformer,
see `knowledge/models/three-model-comparison.md`) explicitly uses
**`correlation_r2`** (squared Pearson) as the reported metric for all three
models, computed identically via one shared code path so the numbers are
genuinely comparable. `coefficient_of_determination` is computed and saved
alongside it in the same output files for anyone who wants to check for
systematic bias separately.

## Practical rule

Before comparing two R² numbers from this project (or reporting one in a
paper), confirm both were computed the same way. When in doubt, recompute
both from raw predictions/targets rather than trusting a label.
