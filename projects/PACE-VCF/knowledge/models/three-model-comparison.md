# Model comparison: XGBoost vs. Spatial-CNN vs. Pixel-Transformer

A colleague trained three architectures on the same chip-tiled dataset:
XGBoost (per-pixel, no spatial context -- the chip-based sibling of
`knowledge/models/xgboost-monte-carlo-feature-selection.md`), a Spatial-CNN,
and a Pixel-Transformer. This note covers how a genuinely comparable metric
was produced across all three, since none of them had one in a mutually
comparable form as trained.

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

## Results

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
