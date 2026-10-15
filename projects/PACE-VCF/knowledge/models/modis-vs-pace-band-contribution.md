---
title: What the PACE-derived bands add over MODIS-equivalent bands
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# What the PACE-derived bands add over MODIS-equivalent bands

## Summary

The project's central question is whether PACE hyperspectral data improves
tree-cover estimates over the MODIS VCF approach. Each model was retrained on
only the **MODIS-style** bands, only the **PACE-style** bands, and both.
**Every model is most accurate with both**, by more than its run-to-run
noise: adding the PACE-style bands to the MODIS-style ones lowers tree-cover
RMSE by **6% (XGBoost), 8% (Spatial-CNN) and 16% (Pixel-Transformer)**.
Either group alone gets most of the way; they are largely redundant.

## Definitions

- **MODIS-style (195 bands):** the MODIS-equivalent metrics in
  `MODIS_Metrics.tif` -- MODIS-like bands and metrics **computed from PACE
  data**, not from the MODIS sensor.
- **PACE-style (280 bands):** the training bands from `PACE_Metrics.tif`
  (74) and `PACE_AltSort_Metrics.tif` (206) -- hyperspectral indices such as red-edge,
  pigment and water indices, and phenology-sorted metrics.
- Groups come from each chip band's `source_modality` tag; bands selected at
  training time with an exclude pattern.

## Results (metrics v4, tree cover, 75 test chips)

Test RMSE (R², coefficient of determination):

| Bands used | Count | XGBoost | Spatial-CNN | Pixel-Transformer |
| --- | --- | --- | --- | --- |
| MODIS-style only | 195 | 4.76 (0.958) | 6.23 (0.928) | 7.31 (0.901) |
| PACE-style only | 280 | 4.91 (0.955) | 6.16 (0.929) | 6.92 (0.911) |
| All, 5-seed mean ± sd | 475 | 4.49 ± 0.02 | 5.71 ± 0.10 | 6.17 ± 0.07 |
| Gain from adding PACE-style to MODIS-style | | 0.27 (6%) | 0.52 (8%) | 1.14 (16%) |

Validation RMSE agrees: all bands (seed 7) 5.37 / 6.76 / 7.07; MODIS-style
only 5.57 / 6.97 / 7.98; PACE-style only 6.00 / 7.19 / 7.81.

- With no MODIS-style bands, XGBoost leans on CCI first
  (`PACEIndex-CCI-Highest3Mean` 21% of gain, `MTCI-Brownest3Mean` 10%): the
  chlorophyll index stands in for dark red reflectance.
- For XGBoost, MODIS-style alone is slightly better than PACE-style alone;
  for the transformer, PACE-style alone is better.

## Limitations and known issues

- Each single-group cell is one training run. Fewer-band neural models vary
  more between runs, so MODIS-only versus PACE-only for the neural models is
  the least certain comparison here; the gain of "both" over either group is
  larger than the measured seed spread.
- Chip-level split: optimistic in absolute terms; relative comparisons on
  the same chips are sound.
- "MODIS-style" bands are computed from PACE observations at PACE timing;
  this is not a comparison with MODIS-sensor data.

## Sources

- Project working code: `chips_v3/launch_style_test_v3.sh` (see
  `examples/scripts/`).
