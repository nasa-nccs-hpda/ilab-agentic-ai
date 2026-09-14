# Dataset: VIIRS VNP21A2 land surface temperature

## What it is

VIIRS (Visible Infrared Imaging Radiometer Suite) VNP21A2, an 8-day
composite Land Surface Temperature (LST) product, supplies the thermal
metrics in this project (referred to throughout as "Band31" metrics, after
the analogous MODIS thermal band).

- **Band used:** Band 31 equivalent, thermal infrared (~11 μm).
- **Native resolution:** 1 km, aggregated to 2 km to match PACE.
- **QA filtering:** `QC_Day` bits 0-1 (MODLAND_QA) and bits 6-7 (LST
  accuracy).

## Role in the pipeline

Thermal metrics (min/max/mean/median, amplitude, temperature-sorted
composites like Warmest3/Coolest3, phenology-linked values like
`ThermalAtPeakNDVI`, and growing-season counts) help the model distinguish
bare ground from forest, since bare/arid surfaces run hotter than vegetated
ones under similar illumination.

## Known limitation

VIIRS thermal coverage is frequently lower than PACE optical coverage for
the same pixel and composite period, because the two instruments have
different orbits, cloud masking, and QA filtering. This project's NaN
handling for thermal gaps (sort-to-infinity tricks, mean fallback for
phenology-indexed values, first-valid-value scanning) is documented in
`knowledge/algorithms/scaling-conventions-and-nan-handling.md`.

Thermal metrics also drove a documented desert/arid over-prediction failure
mode: `LST`-based growing-season-count metrics read similarly high in both
deserts and tropical forests, so an early model version predicted 15-20%
tree cover in deserts (should be ~0%). Mitigated with an explicit
post-processing arid correction (cap predictions where LST is high, NDVI max
is low, and LST range is high).
