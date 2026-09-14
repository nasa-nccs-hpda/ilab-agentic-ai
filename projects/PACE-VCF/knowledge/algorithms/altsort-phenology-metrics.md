# Algorithm: phenology-based metric sorting (AltSort)

## The problem with calendar-based sorting

The original MODIS VCF methodology sorts composites by NDVI (greenness).
This project's first extension sorted composites by calendar month
("UnsortedMonthly": January, February, ...) to see whether monthly
resolution added value beyond greenness-sorting.

**Discovery process:** analyzing Random Forest feature importances on the
calendar-based metrics revealed they don't generalize globally:
- Northern Hemisphere: peak greenness June-August.
- Southern Hemisphere: peak greenness December-February.
- Tropics: multiple or no distinct growing seasons.

A model trained on "August NDVI" as a feature learns a relationship that's
backwards in the Southern Hemisphere. `INCLUDE_UNSORTED = False` excludes
these calendar-based metrics from training as a result.

## The fix: sort by phenology, not the calendar

AltSort metrics use phenological reference points instead of fixed months --
these adapt automatically to each pixel's local growing season and work
globally without manual per-hemisphere adjustment:

| Metric | What it captures |
| --- | --- |
| `AtGreenUp` | Spring leaf-out / start of growing season |
| `AtPeakNDVI` | Maximum productivity |
| `AtMinNDVI` | Dormant season / senescence |
| `Senescence` | Fall transition period |
| `SeasonalRange` | Amplitude of phenological change (deciduous vs. evergreen) |

## Sorting by PACE indices instead of NDVI

Composites are also sorted/selected by hyperspectral indices beyond NDVI,
each capturing a different physiological signal:
- **REIP** (Red Edge Inflection Point): sensitive to chlorophyll content and
  canopy structure differently than NDVI; identified as the #1 predictor
  overall (from IGARSS conference research motivating its inclusion).
- **CCI** (Chlorophyll/Carotenoid Index): pigment ratio, indicates stress and
  seasonality.
- **PRI** (Photochemical Reflectance Index): photosynthetic light-use
  efficiency.

Stress/pigment-based sorts (e.g. `HighChlorophyll3Mean`,
`HighCarotenoid3Mean`, `HighAnthocyanin3Mean`, `MostStressed3Mean`,
`LeastStressed3Mean`) capture vegetation physiological state at specific
points in the growing season rather than just its average value.

## Growing Season Length (GSL)

GSL emerged as an important Random Forest feature. It distinguishes:
- Evergreen (long GSL) vs. deciduous (short GSL).
- Tropical (year-round) vs. temperate (seasonal).
- Desert (minimal GSL) vs. vegetated (substantial GSL).

`ThermalVegGSL` combines a thermal threshold (LST > 280K) with a vegetation
threshold (NDVI > 0.3) to define the season more robustly than either signal
alone.
