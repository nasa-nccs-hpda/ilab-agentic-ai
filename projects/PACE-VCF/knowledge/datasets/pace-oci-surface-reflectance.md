# Dataset: PACE-OCI daily surface reflectance (SURF REF)

## What it is

PACE (Plankton, Aerosol, Cloud, ocean Ecosystem) carries the Ocean Color
Instrument (OCI), a hyperspectral imager. This project uses the L3m daily
Surface Reflectance (SURF REF) product, not PACE's own vegetation-index
products.

- **Spectral range:** 340-895 nm continuous at 2.5 nm resolution, plus 7
  discrete SWIR bands: 940, 1038, 1250, 1378, 1615, 2130, 2260 nm.
- **Resolution:** 2 km (native L3m).
- **Acquisition note:** OCI performs a tilt maneuver at the sub-solar point
  to avoid sun glint.
- **QA filtering:** pre-filtered in the L3m product (ATMFAIL, CLDICE,
  HIGLINT, HILT, HISATZEN, HISOLZEN flags already excluded).

## Why surface reflectance, not PACE's vegetation-index products

PACE's own vegetation index products don't document their QA flag limits, so
this project instead uses surface reflectance directly and computes all
indices (NDVI, REIP, CCI, PRI, etc.) itself, with QA filtering it controls
and can verify.

## MODIS-equivalent band mapping

To compute MODIS-equivalent metrics from PACE's continuous spectrum, PACE
wavelength ranges are mapped to MODIS band definitions:

| MODIS band | Wavelength range (nm) | Role | PACE wavelength used |
| --- | --- | --- | --- |
| Band_1 | 620-670 | Red | -- |
| Band_2 | 841-876 | NIR | -- |
| Band_3 | 459-479 | Blue | -- |
| Band_4 | 545-565 | Green | -- |
| Band_5 | 1230-1250 | SWIR1 | 1249 nm |
| Band_6 | 1610-1652 | SWIR2 | 1618 nm |
| Band_7 | 2105-2155 | SWIR3 | 2131 nm |

**Known limitation, fixed:** Band_6's range was originally `(1628, 1652)`,
which excludes PACE's actual 1618 nm SWIR2 band -- every Band_6 metric was
100% invalid until the range was widened to `(1610, 1652)`. If reproducing
this mapping elsewhere, use the corrected range.

## Limitations

- 2 km native resolution limits spatial detail relative to MODIS VCF's
  underlying 250 m product (aggregated to 2 km for training/comparison in
  this project).
- Persistent cloud cover in tropical regions (e.g. Amazon tiles) produces low
  valid-pixel counts even after compositing.
