# PACE-VCF: project overview

## Goal

Determine whether PACE-OCI hyperspectral surface reflectance can produce a
Vegetation Continuous Fields (VCF) product -- percent tree cover, percent
non-tree vegetation, percent non-vegetated -- competitive with the existing
MODIS VCF (MOD44B Collection 6/6.1) methodology, which relies on a smaller
set of discrete spectral bands.

**Scientific motivation:**
- PACE-OCI offers continuous hyperspectral coverage (340-895 nm at 2.5 nm
  resolution, plus 7 discrete SWIR bands 940-2260 nm) that MODIS's ~7
  discrete bands cannot match.
- Red-edge indices (REIP, NDRE, CIRE, MTCI) are diagnostic for vegetation
  structure and are only computable with contiguous hyperspectral bands.
- Pigment indices (CCI, PRI, mARI) capture physiological vegetation state
  beyond what NDVI alone reflects.

## Experiment roadmap and final status

| # | Experiment | Status | Result |
| --- | --- | --- | --- |
| 1 | MODIS-methodology baseline (Random Forest, MODIS-equivalent metrics only) | Complete | Established baseline R²/RMSE/MAE |
| 2 | MODIS + PACE hyperspectral metrics (XGBoost + Monte Carlo feature selection) | Complete | Full-model R² ~0.80, MC (50-feature) model R² ~0.76; REIP identified as the top predictor |
| 3 | Deep learning (Spatial-CNN, Pixel-Transformer) on chip-tiled data | Complete, compared against Exp. 2's XGBoost | See `knowledge/models/three-model-comparison.md` |
| 4 | PACE + AlphaEarth Foundations embeddings | Complete (pipeline validated, integrated into training) | See `knowledge/datasets/alphaearth-foundations-embeddings.md` |
| 5 | Vision foundation model fine-tuning (DINOv2/v3) | Not started | Out of scope for this shelving point |

The project is being shelved at this point to write up results. Experiment 5
was never started; if the project resumes, it's the natural next step.

## Data flow

```text
PACE L3m (daily surface reflectance) + VIIRS VNP21A2 (8-day LST)
        |
   Composites (2-Composites/)            -- 32-day composites, 12/year
        |
   Metrics TIFs (3-Metrics/)              -- MODIS-equivalent, PACE hyperspectral,
        |                                    AltSort (phenology-sorted), AlphaEarth
   Training parquet / chip dataset
        |
   XGBoost, Spatial-CNN, or Pixel-Transformer model
        |
   VCF predictions (2 km, or 250 m via super-resolution guided by MODIS VCF)
```

Two parallel training data representations exist:
- **"Legacy" (tabular):** one row per 2 km pixel, features read directly from
  the metrics TIFs. Simpler, faster to iterate, used for Experiments 1-2 and
  the AlphaEarth integration.
- **"Chips":** fixed-size image tiles cut from the metrics TIFs, used for the
  Spatial-CNN and Pixel-Transformer models (which need spatial context) and
  also re-used for a chip-based XGBoost baseline so the three-model
  comparison in Experiment 3 is apples-to-apples.

## Notebook families (private repo)

The numbering below reflects the private `PACE_VCF` repository's history, not
this project directory's `examples/`, which holds only a curated subset with
outputs stripped.

- `2c`/`2e` -- composite generation
- `3e`...`3l` -- metrics calculation; `3l` is canonical (see
  `knowledge/troubleshooting/scale-thermal-diff-regression.md` for why `3k`
  was superseded)
- `6h`/`6zg` -- legacy (tabular) training, without/with AlphaEarth
- `6g`/`6zh` -- chips training, without/with AlphaEarth
- `7a`...`7g` -- inference and MODIS-VCF comparison
- `9a` -- super-resolution: guided filter and residual/ratio injection
  (2 km -> 250 m, MODIS-VCF-guided)
- `9b` -- super-resolution: AlphaEarth-embedding regression downscaling
  (no same-tile guide needed)
- `10`/`11` -- three-model comparison (spatial 5-tile R², then true
  15%-holdout R²)

## Key findings

- REIP (Red Edge Inflection Point) is consistently the top predictor across
  the tabular models.
- Thermal metrics (VIIRS LST) help separate bare ground from forest but drive
  a documented desert/arid over-prediction failure mode (see
  `knowledge/troubleshooting/`, project history) unless corrected.
- Phenology-based sorting (AltSort) outperforms calendar-based sorting
  because it generalizes across hemispheres without manual adjustment --
  see `knowledge/algorithms/altsort-phenology-metrics.md`.
- AlphaEarth embedding features are used by the trained models but rank
  below the hand-engineered PACE hyperspectral indices in feature
  importance -- they add information, not a replacement for domain-specific
  indices.
- Several real bugs were found and fixed during development that had
  silently affected reported metrics for a period of time (see
  `knowledge/troubleshooting/`); any number from before the listed fix date
  should be treated as unreliable, not just outdated.

## Super-resolution (2 km -> 250 m)

Explored as a post-processing step, not part of the main VCF prediction
task: can this project's 2 km predictions be downscaled to MODIS VCF's
native 250 m for a future year with no real MODIS VCF to compare against at
all? Three methods were tried and compared. **Two guide-based texture
methods (a guided filter and residual/ratio injection) don't recover real
fine-scale detail and barely or don't beat naive upsampling; a
fine-resolution regression using AlphaEarth embeddings does recover real
detail (visually confirmed) and generalizes to unseen tiles, at roughly
8.8-8.9% RMSE vs. a 9.71% plain-upsample baseline.** Full methodology,
numbers, and comparison figures: `knowledge/models/super-resolution-2km-to-250m.md`.

Several real bugs were found and fixed along the way, each with its own
write-up: a NaN-propagation bug that silently poisoned up to 99% of some
tiles' output (`knowledge/troubleshooting/box-filter-nan-poisoning.md`), a
non-atomic checkpoint write that let a crash masquerade as a completed
result (`knowledge/troubleshooting/non-atomic-checkpoint-writes.md`), two
unrelated GPU/XGBoost failures
(`knowledge/troubleshooting/xgboost-gpu-tree-method-and-arch-mismatch.md`),
and a naive-average-vs-pixel-weighted-RMSE reporting error
(`knowledge/troubleshooting/unweighted-vs-pixel-weighted-rmse.md`).

## Future work

One line of work was scoped but never started before shelving:

- **Experiment 5 (vision foundation model fine-tuning, DINOv2/v3).** Never
  started; see the roadmap table above.

For super-resolution specifically, the concrete next step if this resumes
is building on the AlphaEarth-regression approach rather than the
guide-based methods (see the recommendation at the end of
`knowledge/models/super-resolution-2km-to-250m.md`) -- in particular, a
light spatial-smoothing pass to address its visible pixel-level speckle,
and re-evaluating it under the same within-tile checkerboard design used
for the other two methods so all three are compared on identical evaluation
designs, not just identical tiles.
