---
title: Multi-seed study -- how stable are accuracy and band rankings?
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Multi-seed study: how stable are accuracy and band rankings?

## Summary

One training run gives one sample of a model's accuracy and one sample of its
feature ranking. Retraining each model on all 475 v4 bands at five model
seeds (same chips, same chip split) showed that **accuracy barely depends on
the seed, but the neural models' band rankings depend on it a lot**. XGBoost's
ranking is stable. The models reach the same accuracy with different bands
because the information is spread across many interchangeable bands; single
neural-model band rankings should not be interpreted, while rankings by
band group are stable.

## How it was done

- Model seeds 7 (the original all-band run), 11, 23, 37, 41; chip split fixed
  at seed 7 so the same chips are in train, validation and test every time.
- The colleague's neural training command uses one seed for both the split
  and the model start, so a small wrapper keeps the split seed and changes
  only the model seed
  (`knowledge/troubleshooting/split-seed-tied-to-model-seed.md`). The
  XGBoost command already separates them (`--split-seed`, `--seed`); its
  seed drives 80% row and 80% band subsampling per tree.
- Neural rankings: fuller integrated-gradients XAI on each seed's model.
  XGBoost: gain for tree cover.
- Consensus ranking = bands ordered by mean rank over the five seeds; the
  consensus top 100 became each final model's band list.

## Results (metrics v4, tree cover)

Accuracy across five seeds, test chips:

| Model | R² mean ± sd | RMSE mean ± sd (range) |
| --- | --- | --- |
| XGBoost | 0.9625 ± 0.0004 | 4.49 ± 0.02 (4.47-4.52) |
| Spatial-CNN | 0.939 ± 0.002 | 5.71 ± 0.10 (5.54-5.80) |
| Pixel-Transformer | 0.929 ± 0.002 | 6.17 ± 0.07 (6.10-6.27) |

Ranking stability:

| | XGBoost | Spatial-CNN | Pixel-Transformer |
| --- | --- | --- | --- |
| Top-50 bands shared by two seeds (mean) | 42 | 21 | 14 |
| Spearman correlation of full rankings between seeds | 0.94 | 0.57 | 0.28 |
| Bands in the top 50 of all 5 seeds | 36 | 8 | 1 |
| Bands in the top 100 of all 5 seeds | 71 | 21 | 3 |
| Consensus top 100 shared with the seed-7 top 100 | 90 | 63 | 61 |

Importance by band group (% of each model's total, mean ± sd over seeds):

| Group | XGBoost | Spatial-CNN | Pixel-Transformer | % of the 475 bands |
| --- | --- | --- | --- | --- |
| Band 1 (red) | 63 ± 2 | 3 | 9 ± 5 | 4 |
| Band 7 (SWIR 2130 nm) | 16 ± 2 | 5 | 8 ± 5 | 6 |
| PACE red-edge indices (REP, REIP, NDRE, MTCI, CIRE) | 7 | 21 ± 0.5 | 11 ± 4 | 24 |
| PACE pigment indices (CCI, PRI, mARI, GCI) | 4 | 19 ± 0.7 | 22 ± 3 | 17 |
| PACE water indices (NDWI, NDII) | 2 | 12 | 6 | 9 |
| Thermal (Band 31 / LST) | 1 | 3 | 10 ± 2 | 3 |
| Band 4 (green) | 1 | 3 | 13 ± 5 | 4 |
| MODIS-style / PACE-style overall | 86 / 14 | 39 / 61 | 58 / 42 | 41 / 59 |

- XGBoost follows the classic MODIS VCF signal: most importance on red
  reflectance, 56% on dormant- or lowest-season composites.
- The neural models spread importance over PACE indices. The Spatial-CNN's
  group shares vary by less than 1% between seeds even though only 8 bands
  are in all five of its top-50 lists.
- Greenest-season composites carry about a quarter of importance in all
  three models.

## Practical rules

- Do not interpret a single neural model's top-N band list; use a
  multi-seed consensus, and prefer statements about band groups.
- A drop in neural accuracy between two variants smaller than about 0.1 RMSE
  (all-band) is within run-to-run noise. Models with fewer bands vary more.
- XGBoost's ranking from one run is usable.

## Limitations and known issues

- XGBoost importance is gain; neural importance is integrated gradients.
  Compare patterns within a model, not percentages across model types.
- Groups here are by spectral region and index family, not by measured
  correlation; grouping by correlation (e.g. |r| > 0.95) is a natural next
  step.
- Five seeds, one data split; chip-level split is optimistic.

## Sources

- Project working code: `chips_v3/launch_seed_study_v3.sh`,
  `chips_v3/train_seed_v3.sbatch`, `chips_v3/train_init_seed.py`,
  `chips_v3/combine_seed_rankings.py` (see `examples/scripts/`).
- Consensus top-50 lists: `examples/feature_importance_v4_consensus.txt`.
