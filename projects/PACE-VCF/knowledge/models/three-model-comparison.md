# Model comparison: XGBoost vs. Spatial-CNN vs. Pixel-Transformer

A colleague trained three architectures on the same chip-tiled dataset:
XGBoost (per-pixel, no spatial context -- the chip-based sibling of
`knowledge/models/xgboost-monte-carlo-feature-selection.md`), a Spatial-CNN,
and a Pixel-Transformer. This note covers how a genuinely comparable metric
was produced across all three, since none of them had one in a mutually
comparable form as trained.

## Current results: metrics v4 (October 2026)

The three models were retrained on the v4 metrics (475 bands; see
`knowledge/algorithms/metrics-v4-definitions-and-duplicate-bands.md`) with
the colleague's code and settings unchanged: 30 epochs, Huber loss, batch 4
for the neural models; XGBoost 500 trees, depth 10, learning rate 0.1, early
stopping 30, one booster per target, on GPU. Same 504 chips and the same
seed-7 70/15/15 chip-level split (353 / 76 / 75 chips). **Tree cover only.**

**Chip-level test scores** (75 test chips, 287,332 pixels; R² here is the
coefficient of determination):

| Model | All 475 bands, seed 7: RMSE (R²) | All bands, 5 model seeds: RMSE mean ± sd | Final model (own consensus top 100): RMSE (R²) |
| --- | --- | --- | --- |
| XGBoost | 4.51 (0.962) | 4.49 ± 0.02 | 4.56 (0.961) |
| Spatial-CNN | 5.80 (0.938) | 5.71 ± 0.10 | 5.83 (0.937) |
| Pixel-Transformer | 6.11 (0.931) | 6.17 ± 0.07 | 6.37 (0.925) |

- XGBoost is ahead of both neural models, as in v2.
- Removing the duplicate bands cost nothing: XGBoost's v4 scores match v3 to
  within 0.01 RMSE; the neural changes are within their seed spread.
- The final models use each model's own consensus top-100 bands from the
  multi-seed study (`multi-seed-ranking-stability.md`; band count from
  `band-count-sweep.md`). The Spatial-CNN final is the best of six 100-band
  runs **on the validation chips** (see
  `knowledge/troubleshooting/single-run-final-model-unlucky-draw.md`).
- The chip split is by chip, not by tile, so most tiles have chips in both
  training and test: chip scores are optimistic. Use them to compare
  variants, not as absolute accuracy.

**Full-tile scores** (2 km maps from the three final models, scored against
MODIS VCF C6 2020 tree cover; 280 tiles, 38.6 M pixels with a valid label
and real inputs for every model; **r² here is squared Pearson**, pooled RMSE
is pixel-weighted):

| Model | Pooled RMSE | Pooled bias | Median tile r² |
| --- | --- | --- | --- |
| XGBoost (v4 final) | 6.76 | +0.41 | 0.681 |
| Pixel-Transformer (v4 final) | 7.39 | +0.44 | 0.637 |
| Spatial-CNN (v4 final) | 7.55 | -0.79 | 0.656 |

- Full-tile scores are far below chip scores for every model: full tiles
  cover the globe, mostly away from the training chips.
- On identical pixels, the v4 XGBoost equals the earlier versions (v3 final
  6.74; on the 251 tiles every version covers, v4 6.90 vs the shelved-era
  chipped XGBoost 6.90). The v4 transformer is better than v3 (7.39 vs 7.58);
  the v4 Spatial-CNN is worse than v3 (7.55 vs 7.22) and under-predicts tree
  cover -- an open question (see `knowledge/overview/project-overview.md`,
  Future work).
- Pixels where a model's inputs were mostly missing are excluded; see
  `knowledge/troubleshooting/median-imputed-pixels-in-full-tile-scoring.md`.
- 289 of 291 tiles have maps; two polar tiles are refused
  (`knowledge/troubleshooting/polar-tiles-empty-bands.md`); 9 more have no
  scorable pixels.

Everything below this point describes the shelved-era (v2) comparison and
how a comparable metric was first built; its numbers predate the v3/v4
metric fixes.

## The comparability problem

- The two Lightning-trained models (Spatial-CNN, Pixel-Transformer) only had
  loss/MAE/RMSE logged from `trainer.test()` -- no R² at all, and pooled
  across all three output bands rather than per-band.
- XGBoost had per-band R² logged, but using a codebase that defines two
  different R² quantities (see `knowledge/algorithms/two-r2-definitions.md`).
- An initial attempt compared 5-tile spatial-inference R² across the three
  models. This is a real, useful number, but it isn't the true held-out
  generalization metric -- it doesn't correspond to a frozen 15% test split
  from training.

## What was actually done

Real inference was re-run against each model's own saved artifacts,
identically, filtered to the exact chip-level 15% test split frozen at
training time (`toy_model_split == "test"` in each run's own manifest):

- **XGBoost:** load the saved per-band boosters directly and predict on the
  test-split chips. This exactly reproduces the run's own logged test R² --
  used as a sanity check that the reproduction methodology is correct before
  trusting the other two models' numbers.
- **Spatial-CNN / Pixel-Transformer:** reconstruct the exact trained network
  from its saved checkpoint plus the run's config (input normalization,
  nodata/water masking read from the run's own saved stats, not
  hardcoded), and run real forward-pass inference on the same frozen test
  split.

All three use **`correlation_r2`** (squared Pearson correlation) as the
headline metric, per project decision -- see
`knowledge/algorithms/two-r2-definitions.md` for why this specific choice
was made and what it does/doesn't capture.

**A non-obvious pitfall found while building this:** the Lightning-trained
models' per-band target names aren't persisted anywhere in their saved
config (unlike XGBoost's, which does save them) -- they have to be re-derived
the same way training derived them originally: reading the band descriptions
directly off the label raster of a test record, not assumed from position.
Code that instead fell back to generic `band_1`/`band_2`/`band_3` labels
would have been correct numerically but mislabeled which VCF output each
number belongs to.

## Results (v2, historical)

Target bands: `Percent_Tree_Cover`, `Percent_NonTree_Vegetation`,
`Percent_NonVegetated`.

| Target band | XGBoost | Spatial-CNN | Pixel-Transformer |
| --- | --- | --- | --- |
| Percent_Tree_Cover | 0.963 | 0.941 | 0.936 |
| Percent_NonTree_Vegetation | 0.849 | 0.734 | 0.726 |
| Percent_NonVegetated | 0.903 | 0.833 | 0.831 |

(`correlation_r2`, true 15%-holdout test split, one shared model/run per
column.) XGBoost's numbers are directly confirmed against its own logged
`metrics_summary.csv` (exact match). The Spatial-CNN/Pixel-Transformer
numbers come from the band-order fix described above and are very likely
correctly mapped (same label raster, same manifest, same band order as
XGBoost's confirmed set) but were not re-visually-confirmed with real band
names printed after the fix landed -- re-run and confirm the printed table
shows real names, not `band_1`/`band_2`/`band_3`, before quoting these in a
paper.

**Reading:** XGBoost is competitive with, and slightly ahead of, both neural
architectures on this dataset and split -- the added spatial context in the
Spatial-CNN and Pixel-Transformer doesn't yield a clear accuracy advantage
over a per-pixel gradient-boosted-tree baseline here. `Percent_Tree_Cover`
is the best-predicted output across all three models; `Percent_NonTree_Vegetation`
is consistently the hardest.
