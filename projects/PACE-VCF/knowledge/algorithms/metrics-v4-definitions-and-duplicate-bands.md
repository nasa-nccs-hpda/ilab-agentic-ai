---
title: Metrics v4 -- duplicate bands removed, metrics computed as named
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Metrics v4: duplicate bands removed, metrics computed as named

## Summary

In the v2/v3 metrics, **100 of the 521 bands used for training were exact
copies of another band** (35 groups of identical bands). About 70 came from
metrics that did not compute what their names said; about 30 were one
quantity stored under two names. Duplicates inflate apparent importance (a
feature selector keeps picking copies of the same thing), split attribution
arbitrarily between copies, and make feature rankings hard to defend.

Metrics v4 (October 2026) removes the duplicates and computes the amplitude
and median metrics as their names describe. Result: **475 training bands, no
exact duplicates, and no loss of accuracy** (`knowledge/models/three-model-comparison.md`).

## How the duplicates were found

Each band of 40 training chips was compared with every other band for exact
equality (seconds of work on chips; reading 521 bands from full-tile stacks
one at a time was far slower). Bands were grouped when identical on every
pixel of every chip.

## The v4 definitions

X is a band or index; the key is NDVI (greenness), temperature, or the PACE
sort index. Only composites where both X and the key are valid take part.

| Metric family | v2/v3 code computed | v4 computes |
| --- | --- | --- |
| Amplitude variants (`AmpGreenestBandRefl`, `AmpWarmestBandRefl`, PACE-index `AmpGreenness`, `AmpAnthocyanin`, `AmpPigmentRatio`, `AmpStress`) | absolute max minus min of X, which ignores the key and so duplicated other amplitude bands | **X at the highest-key composite minus X at the lowest-key composite**, signed (e.g. greenest minus least green) |
| Median variants (`BandReflMedianGreenness`, `BandReflMedianTemp`) | plain median of X, identical to `BandReflMedian` | **X at the median-ranked composite of the key** (ascending valid composites, element `n_valid // 2`) |

The intent comes from the MODIS VCF reference code (the `modis_vcf`
repository's v1.2.0 branch, `model/Metrics.py`), whose descriptions say
"amp == value 8 - value 1" after sorting by NDVI, and "band x reflectance
associated with median greenness". That code itself runs an absolute
amplitude and a plain median (its rank-based median is commented out as too
slow), so **v4 deliberately differs from the reference code's current
behaviour** to match its stated intent. The original C code uses yet another
scheme (six group statistics, with amplitude = mean of the top two minus
mean of the next two composites).

## Other v4 changes

- **46 bands removed** from the training set: one copy of each
  same-quantity-two-names pair (e.g. `<Index>-SeasonalRange` kept as
  `<Index>-Amp`; `CCI-HighChlorophyll3Mean` = `CCI-Greenest3Mean`;
  `CrossIndex-NDWI-WetSeason/DrySeason` = `NDWI-Max/Min`;
  `<Index>-Brownest` = `<Index>-AtMinNDVI`), the NDVI-sorted-by-itself
  copies, and three self-sorted amplitude variants.
- **Renames:** `PACEIndex-<Index>-Greenest3Mean` became
  `PACEIndex-<Index>-Highest3Mean` (12 bands; "greenest" was wrong for
  indices sorted by their own value), and the PACE-file copy of
  `REP/REIP-Brownest3Mean`, which shared its name with the AltSort copy,
  became `-Lowest3Mean`.
- File layout is unchanged: three files per tile (MODIS_Metrics 298 bands,
  PACE_Metrics 146, PACE_AltSort_Metrics 206), int16, same scaling (see
  `scaling-conventions-and-nan-handling.md`). Training excludes the
  `Unsorted` (calendar) and `QA_` bands, leaving 475.

## How v4 was checked

- Unit tests for the new rank-based functions (18 tests) plus the v3 tests.
- A v3-vs-v4 regression on three tiles: 73 bands changed, all of them
  intended; 563 identical; renamed bands identical to their old values; zero
  exact-duplicate bands remain.
- Chips rebuilt from v4: same 504 chip IDs and labels as before, so the
  seed-7 train/validation/test split is unchanged and results are comparable.

## Limitations and known issues

- Only exact duplicates were removed. Near-duplicates remain (e.g. 3-, 6- and
  8-composite means of the same band), which is one reason neural band
  rankings shift between training runs
  (`knowledge/models/multi-seed-ranking-stability.md`).
- The 175 `Unsorted`/`QA_` bands were not scanned for near-duplicates.
- Two polar tiles now have more fully empty bands than in v3 (h11v01: 75 vs
  61; h24v01: 56 vs 40); both are refused by inference in v3 and v4 alike
  (`knowledge/troubleshooting/polar-tiles-empty-bands.md`).

## Sources

- `modis_vcf` repository, branch v1.2.0, `model/Metrics.py` (NASA NCCS HPDA;
  internal).
- Project working code: `run_metrics_generation_v4.py`, notebook
  `3n_metrics_v4_no_duplicates.ipynb` (see `examples/`).
