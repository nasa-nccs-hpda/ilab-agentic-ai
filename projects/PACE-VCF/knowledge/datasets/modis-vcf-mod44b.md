# Dataset: MODIS VCF (MOD44B) -- training/reference target

## What it is

MOD44B, the MODIS Vegetation Continuous Fields product, is this project's
training label and reference product.

- **Product:** MOD44B, Collection 6 or 6.1 depending on notebook (see
  individual notebooks -- Collection 6, year 2020, is the version most
  commonly used for the PACE-vs-MODIS inference comparison).
- **Native resolution:** 250 m, aggregated (block-mean, 8x8 -> 1) to 2 km to
  match PACE for training and comparison.
- **Outputs used:** Percent_Tree_Cover (0-100%); Percent_NonTree_Vegetation
  and Percent_NonVegetated are also modeled in the three-model comparison
  (`knowledge/models/three-model-comparison.md`) but the legacy/tabular
  XGBoost pipeline trains on Percent_Tree_Cover alone.

## Extraction

Percent_Tree_Cover is pulled from the MOD44B HDF4 subdataset via
`gdalinfo`/`gdal_translate` (subdataset name search for
`Percent_Tree_Cover`). This step silently fails (empty subdataset list, no
error surfaced) if the GDAL install in use lacks HDF4 driver support --
see the pip/environment entries under `knowledge/troubleshooting/` for why
that can happen unpredictably across kernels on a shared HPC system.

## Year mismatch

PACE-VCF training/inference runs for a given processing year (e.g. 2025) are
compared against MOD44B for whatever MODIS VCF year is available and
suitable as ground truth (e.g. 2020) -- these are not the same year. This is
a deliberate simplification (2025 MODIS VCF wasn't available/finalized at
the time), not a data error, but it means absolute agreement metrics include
some real land-cover change between the two years, not just model error.

## Limitations

- Per-tile performance varies by biome: good agreement in mixed
  forest/shrubland (e.g. `h10v05`, `h31v11`), degraded agreement in deserts
  and tropical/cloud-heavy regions due to biome-specific failure modes
  (arid over-prediction; low valid-pixel count from persistent cloud cover).
