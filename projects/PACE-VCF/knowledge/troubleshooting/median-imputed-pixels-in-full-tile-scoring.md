---
title: Full-tile scores swamped by median-filled no-data pixels
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: full-tile scores swamped by median-filled no-data pixels

## Symptom

Not a crash. When the v3 chip models' global maps were first scored against
MODIS VCF, the v3 XGBoost looked far worse than its v2 predecessor (pooled
RMSE 10.9 vs 6.9), although the two had near-identical chip scores. Some
tiles showed a flat prediction over almost the whole tile -- 51.5% tree cover
across 98% of h31v13 -- while the label there was a near-constant ~10%.

## Confirmed cause

The colleague's full-tile inference fills any missing input band with that
band's **tile median** before predicting. Where PACE has no usable data at
all, every input is filled, so the model predicts one constant value, which
was then scored against the label as if it were a real prediction. The
earlier (v2) comparison notebook had excluded those pixels only by accident:
its tabular model produced no value there.

## Resolution

The inference tool writes a per-tile `imputed_feature_fraction.tif` (share of
a pixel's input bands that were filled). Full-tile scoring now keeps a pixel
only if, **for every model being compared**, at most half of its inputs were
filled (`MAX_IMPUTED_FRACTION = 0.5`), the label is valid (no nodata, no
water), and the prediction is finite. All models in a table are scored on
identical pixels. With this mask, v3 and v2 XGBoost were level (6.84-6.90).

Four "flat 10%" tiles (h06v03, h07v03, h28v03, h29v03) have only 103-1,718
real-data pixels out of 360,000; treat their maps as unreliable.

## General lesson

When an inference step silently imputes inputs, its output covers pixels the
model never really saw. Before scoring a map, find out where inputs were
filled and mask those pixels -- and score competing models on the same
pixels, or the comparison measures masks, not models.
