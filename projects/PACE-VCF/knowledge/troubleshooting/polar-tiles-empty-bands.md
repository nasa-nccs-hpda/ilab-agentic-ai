---
title: Polar tiles refused by inference (bands empty for the whole tile)
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: polar tiles refused by inference

## Symptom

Global inference produces no map for some extreme-latitude tiles. The log
shows, for example:

```text
ValueError: tile h11v01 cannot use per-tile median imputation;
19 band(s) have no valid pixels: 'BandReflMaxTemp-Band_6', ...
```

With the v4 final models, 289 of 291 tiles get maps; h11v01 and h24v01 are
refused by all three models.

## Confirmed cause

The colleague's inference fills missing inputs with the tile median of each
band. If a band a model uses has **no valid pixel anywhere in the tile**,
there is no median, and the tile is refused. At these latitudes PACE has few
usable observations, so whole-tile empty bands occur -- 6 to 19 per model
here, mostly thermal (Band 31 / LST), warmest-season and
"at first snow-free" bands.

## Resolution

None applied; the two tiles are reported as missing. History: the v2 chip
models were refused on 32 polar tiles; every v3 and v4 model is refused on
only these 2, including a model using all bands. The v3 metric changes are
responsible, but which change fills those bands was not identified. v4 has
slightly more fully empty bands on these two tiles than v3 (h11v01 75 vs 61;
h24v01 56 vs 40).

## General lesson

Per-tile imputation fails on tiles where an input band is entirely empty.
For global products, check band validity per tile before inference, and
decide explicitly whether to drop such tiles, use a global fallback value,
or use a model without those bands.
