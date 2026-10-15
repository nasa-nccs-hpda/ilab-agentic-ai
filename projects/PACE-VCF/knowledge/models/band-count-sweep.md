---
title: Band-count sweep -- how many input bands each model needs
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Band-count sweep: how many input bands each model needs

## Summary

Each of the three chip models was retrained on only its own top-N tree-cover
bands (N = 10, 25, 50, 100, 200) and compared with the same model on all 475
v4 bands. **XGBoost levels off by 50-100 bands; the Spatial-CNN reaches its
plateau at about 100; the Pixel-Transformer's best point is about 200.** The
project owner chose **100 bands for all three** final models.

## How it was done

- Rankings, tree cover only: XGBoost by gain from its all-band model; the
  neural models by integrated-gradients attribution from a "fuller" XAI run
  (all 76 validation chips, 64 integration steps, best checkpoint; the
  8-chip XAI that runs during training is too noisy for this).
- Bands were selected at training time with the training code's
  exclude-band pattern, from the same chips, so no new chips were needed.
- Same chips, seed-7 split and settings as the all-band models; one training
  run per point.

## Results (metrics v4)

Tree-cover R² (coefficient of determination) on the 75 test chips:

| Bands | 10 | 25 | 50 | 100 | 200 | 475 (all) |
| --- | --- | --- | --- | --- | --- | --- |
| XGBoost | 0.920 | 0.949 | 0.959 | 0.961 | 0.963 | 0.962 |
| Spatial-CNN | 0.846 | 0.909 | 0.922 | 0.938 | 0.935 | 0.938 |
| Pixel-Transformer | 0.899 | 0.918 | 0.925 | 0.925 | 0.933 | 0.931 |

Test RMSE: XGBoost 6.55 / 5.26 / 4.71 / 4.57 / 4.50 / 4.51; Spatial-CNN
9.11 / 7.01 / 6.50 / 5.77 / 5.92 / 5.80; Pixel-Transformer 7.39 / 6.64 /
6.38 / 6.36 / 6.00 / 6.11.

- XGBoost on 25 bands beats both neural models on all 475.
- The Spatial-CNN is the most sensitive to a small band set (0.846 with 10
  bands).
- On the v3 metrics (with 100 duplicate bands) the CNN kept gaining up to
  200 bands; on v4 it levels off at about 100. With one run per point this
  is suggestive, not established.

## Limitations and known issues

- One run per point. A later check showed the 100-band Spatial-CNN's test
  RMSE ranging from 5.77 to 6.44 across three model seeds, so differences of
  about 0.005-0.01 R² between neighbouring neural points are not reliable
  (`multi-seed-ranking-stability.md`,
  `knowledge/troubleshooting/single-run-final-model-unlucky-draw.md`).
- The neural rankings that define "top N" are themselves unstable between
  seeds; the final models therefore use consensus rankings over five seeds.
- Chip-level split: optimistic in absolute terms.

## Sources

- Project working code: `chips_v3/launch_sweep_v3.sh`,
  `chips_v3/make_topn_lists.py`, `presentations/plot_band_sweep.py` (see
  `examples/scripts/`).
