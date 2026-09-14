# Troubleshooting: test-set leakage in Monte Carlo feature selection

## Symptom

Not a crash or an obviously-wrong number -- a subtly optimistic one. Asking
"is the reported R² train or test, and is there a genuine holdout?" surfaced
the issue; nothing about the printed output made it visible on its own.

## Confirmed cause

Two of the four training notebooks (the "legacy"/tabular family) used a
single 80/20 `train_test_split` (fixed `random_state`, so deterministic and
identical across calls). That same 20% test set was reused for three
different purposes:

1. Scoring the "full model."
2. Scoring **every one** of the 100 Monte Carlo trials -- and each trial's
   test-set score is exactly what determines which features get counted as
   "used" and make the final top-N feature list.
3. Scoring the final selected-feature model, reported as "test R²."

Because the test set indirectly shaped which features got selected in step
2, the "test R²" reported in step 3 is not a clean, untouched holdout --
it's mildly optimistic (a standard feature-selection-leakage pattern).

The other two training notebooks (the "chips"/image family) already used a
correct three-way split and were not affected -- comparing the two families
side by side is what made the gap visible.

## Resolution

Refactored both affected notebooks to the same clean 70/15/15 split already
in use by the unaffected pair: train fits every model, validation scores the
Monte Carlo trials and drives feature selection, and test is touched only
once, for the one final reported number.

While applying this fix, a second, unrelated issue was found in the two
notebooks that already had the correct split: leftover cells from before
their own 70/15/15 refactor were still present, calling old two-way-split
function signatures that no longer matched the (already-updated) function
definitions. These cells would raise `TypeError` if executed and were
deleted as dead code.

## General lesson

When the same held-out set is used both to *choose* something (features,
hyperparameters, early-stopping point) and to *report* a final number, the
reported number is not a clean generalization estimate, even if it's never
used to fit model weights directly. This requires a third split, not just a
guarantee that "the test set was never in `.fit()`."
