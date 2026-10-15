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

## Experiment roadmap and status

| # | Experiment | Status | Result |
| --- | --- | --- | --- |
| 1 | MODIS-methodology baseline (Random Forest, MODIS-equivalent metrics only) | Complete (v2 metrics) | Established baseline R²/RMSE/MAE |
| 2 | MODIS + PACE hyperspectral metrics (XGBoost + Monte Carlo feature selection) | Complete (v2 metrics); re-run on v4 | v2: full-model R² ~0.80, MC (50-feature) model R² ~0.76. v4: see `knowledge/models/xgboost-monte-carlo-feature-selection.md` |
| 3 | Deep learning (Spatial-CNN, Pixel-Transformer) on chip-tiled data | Complete; redone on v4 metrics | See `knowledge/models/three-model-comparison.md` |
| 4 | PACE + AlphaEarth Foundations embeddings | Complete (v2 metrics; pipeline validated, integrated into training) | See `knowledge/datasets/alphaearth-foundations-embeddings.md` |
| 5 | Vision foundation model fine-tuning (DINOv2/v3) | Not started | -- |
| 6 | Metrics v3: sort and scaling fixes | Complete | Changed feature rankings far more than accuracy (red edge returned to the rankings once saturated REP/REIP bands were fixed) |
| 7 | Metrics v4: duplicate bands removed, metrics redefined to their original intent | Complete (October 2026) | `knowledge/algorithms/metrics-v4-definitions-and-duplicate-bands.md` |
| 8 | v4 model study: band-count sweep, multi-seed ranking stability, MODIS-only vs PACE-only, final models, global 2 km maps | Complete (October 2026) | `knowledge/models/band-count-sweep.md`, `multi-seed-ranking-stability.md`, `modis-vs-pace-band-contribution.md`, `three-model-comparison.md` |

The project was shelved for write-up after Experiment 4 and resumed in
September/October 2026 to correct the metrics (v3, then v4) and redo Experiments 2-3
on them. Experiment 5 is still the natural next modelling step.

## Metrics versions

The same 291 MODIS-VCF land tiles and the same composites underlie every
version; only the metrics computed from them change. Each version is a
separate output folder (`3-Metrics/`, `3-Metrics-v3/`, `3-Metrics-v4/`), and
models trained on one version cannot read another (band lists differ).

| Version | Bands used in training | What changed |
| --- | --- | --- |
| v2 | 521 | The shelved-era metrics. 100 of the 521 bands turned out to be exact copies of others. |
| v3 | 521 | Sort and scaling fixes (a cross-sort bug that made CCI "3-mean" metrics byte-identical copies; saturated REP/REIP bands). Same band names as v2. |
| v4 | 475 | Duplicates removed; amplitude and median metrics computed as their names describe; some bands renamed. See the v4 algorithm note. |

"Bands used in training" excludes the `Unsorted` (calendar) and `QA_` bands,
as in the colleague's chipping code.

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

From v3 on, the chip pipeline is a colleague's chipping, training,
XAI and full-tile inference packages, called in place and unchanged; this
project adds launchers, checks and comparisons around them:

```text
3-Metrics-v4/ (291 tiles)
   |-- chips: 504 chips from 63 training tiles, 475 bands, seed-7 70/15/15 chip split
   |      |-- train all bands (3 models) -> XAI -> band-count sweep
   |      |-- multi-seed study (5 seeds) -> consensus top-100 band lists
   |      `-- final models (consensus top 100 each)
   `-- full-tile stacks (input_stack_2km.tif per tile, 475 bands, chip band order)
          `-- global inference with the final models -> 2 km tree-cover maps
                 `-- comparison against MOD44B on pixels with real inputs
```

How to run it on NCCS: `skills/run-pace-vcf-pipeline/`.

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

v4 (current; details in the linked pages):

- **Adding the PACE-derived metrics to the MODIS-equivalent ones improves
  every model**, by more than run-to-run noise: tree-cover RMSE drops 6%
  (XGBoost), 8% (Spatial-CNN) and 16% (Pixel-Transformer). Either group alone
  gets most of the way -- they are largely redundant
  (`knowledge/models/modis-vs-pace-band-contribution.md`).
- **XGBoost is the most accurate model** on chips and on full tiles, and it
  rediscovers the classic MODIS VCF signal: about 63% of its importance is
  Band 1 (red), mostly dormant-season composites. The neural models spread
  importance over PACE red-edge, pigment and water indices.
- **Neural band rankings from one training run are not reliable**; accuracy
  is stable across seeds but the top-50 bands are not
  (`knowledge/models/multi-seed-ranking-stability.md`). Interpret neural
  feature importance by band group, not single bands.
- **Removing the 100 duplicate bands (v4) cost nothing in accuracy** and
  makes the rankings defensible.
- Full-tile scores are far below chip scores for every model (chip test R²
  ~0.92-0.96 vs full-tile median r² ~0.64-0.68): chips come from training
  areas with a chip-level split, full tiles cover the globe.

v2 (historical, shelved-era):

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

Open items from the v4 work (October 2026):

- **v4 Spatial-CNN on full tiles.** It is less accurate than the v3 CNN
  globally (pooled RMSE 7.55 vs 7.22 on identical pixels) and now
  under-predicts tree cover (bias -0.79), although its chip scores are
  normal. A 100-band CNN varies a lot between training runs; an all-band CNN
  is steadier. Not yet investigated.
- **Tile-level evaluation.** The chip split puts chips from the same tile in
  train and test, so chip scores are optimistic. A split by whole tile would
  give a more honest held-out score.
- **Feature importance by correlated-band group** rather than single bands,
  which the multi-seed study suggests is the stable level of interpretation.
- **Two polar tiles (h11v01, h24v01)** still get no map
  (`knowledge/troubleshooting/polar-tiles-empty-bands.md`).

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
