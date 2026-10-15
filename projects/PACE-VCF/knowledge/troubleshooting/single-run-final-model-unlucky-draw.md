---
title: A final model looked 0.7 RMSE worse -- an unlucky training run
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: a final model looked 0.7 RMSE worse -- an unlucky training run

## Symptom

The v4 final Spatial-CNN, trained on its consensus top-100 bands, scored
tree-cover test RMSE 6.44 (R² 0.923). The same architecture on its seed-7
top-100 list had scored 5.77 in the band-count sweep, and on all bands
5.71 ± 0.10 across five seeds. The other two final models matched
expectations. Either the consensus band list was bad for the CNN, or this
one run was unlucky.

## Confirmed cause

A check retrained the CNN on **both** lists at two more model seeds (same
chip split), giving three runs per list. Tree-cover RMSE, test (validation):

| List | seed 7 | seed 11 | seed 23 | test mean | validation mean |
| --- | --- | --- | --- | --- | --- |
| Consensus top 100 | 6.44 (6.92) | 5.94 (6.75) | 5.83 (6.67) | 6.07 | 6.78 |
| Seed-7 top 100 | 5.77 (6.82) | 6.22 (7.13) | 6.02 (6.82) | 6.00 | 6.92 |

The two lists are equal within noise. A 100-band CNN simply varies a lot
between training runs (5.77-6.44 here) -- far more than on all 475 bands
(± 0.10). The 6.44 was one unlucky draw.

## Resolution

The project owner chose, as the final CNN, the run with the best
**validation** score among the six: consensus list, model seed 23
(validation 6.67, test 5.83, R² 0.937). Choosing on test would have
overstated its accuracy.

## General lesson

Before trusting a single final training run, compare it with the sweep
result and the measured seed spread; when it is out of line, retrain at a
few more seeds before blaming the inputs. Pick among runs on validation,
never on test. Models with fewer input bands can be much noisier than their
all-band versions.
