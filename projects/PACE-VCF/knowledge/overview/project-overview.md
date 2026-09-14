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
- `9` -- experimental super-resolution (2 km -> 250 m, MODIS-VCF-guided)
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

## Future work

Two lines of work were started or scoped but not completed before shelving.
Neither is represented in `examples/` -- there are no validated results to
show for either yet.

- **Super-resolution (2 km -> 250 m).** Notebook `9` builds a pipeline to
  downscale 2 km VCF predictions to MODIS VCF's native 250 m, using MODIS
  VCF Collection 6 (2020) as a guide raster via a Fast Guided Filter
  implementation. It includes region-stratified train/test tile splitting
  (guide and evaluation tiles drawn from distinct geographic regions, not
  just distinct pixels) and a non-circular checkerboard-holdout validation
  design (guide and held-out test pixels interleaved within the same tile,
  so the guided filter isn't evaluated on the same pixels it was tuned
  against), with a hyperparameter search over guide-filter radius/epsilon
  restricted to guide tiles only. **Motivation:** for future years with no
  real MODIS VCF product to compare against (e.g. 2026), a downscaling model
  calibrated on years that do have MODIS VCF could produce a
  MODIS-VCF-*like* 250 m product from this project's 2 km predictions. The
  pipeline is built but has not been run end-to-end for real -- validating
  it (and deciding whether the checkerboard design generalizes across
  biomes) is the concrete next step if this line of work resumes.
- **Experiment 5 (vision foundation model fine-tuning, DINOv2/v3).** Never
  started; see the roadmap table above.

Of the two, the super-resolution pipeline is further along and would likely
be faster to validate.
