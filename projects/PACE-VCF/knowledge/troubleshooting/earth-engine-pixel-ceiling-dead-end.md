# Troubleshooting: Earth Engine cannot aggregate AlphaEarth to 2 km

## Symptom

Attempting to aggregate AlphaEarth Foundations embeddings (10 m native) to
this project's 2 km working resolution via Earth Engine's
`reduceResolution()` + `setDefaultProjection()` eventually fails with:

```text
Number of pixels requested from Image.setDefaultProjection exceeds the
maximum allowed (2^31)
```

This happens even when using `Export.image.toAsset` (async) instead of a
synchronous download, and even after clipping to the target region first.

## Confirmed cause

This is structural, not a bug or a parameter-tuning problem. A full ~1112 km
MODIS sinusoidal tile at AlphaEarth's 10 m native resolution is
`(1,112,000 / 10) ^ 2 ≈ 12.4 billion` native pixels -- larger than Earth
Engine's hard `2^31 ≈ 2.1 billion` pixel ceiling on
`Image.setDefaultProjection`, regardless of how the request is chunked,
scaled with `tileScale`, or exported asynchronously. Google's own tutorial
for this exact dataset recommends `Export.image.toAsset` for large exports,
and that does get further (the export genuinely runs for many minutes) --
but it still hits the same ceiling once the underlying computation executes,
confirming it's a genuine pixel-count ceiling, not a synchronous-request-size
limit.

## Resolution: don't use Earth Engine's compute API for this

Read AlphaEarth's raw Cloud-Optimized GeoTIFFs directly from the public GCS
bucket instead -- no Earth Engine account, OAuth, or billing project needed.
See `knowledge/datasets/alphaearth-foundations-embeddings.md` for the
working approach (bucket layout, de-quantization formula, aggregation
method).

## Error chain encountered before finding the real limit (kept for reference)

In case a *smaller* region ever needs revisiting via Earth Engine:

1. `Projection: The CRS of a map projection could not be parsed` -- Earth
   Engine's CRS parser wants an EPSG code or WKT, not a raw PROJ4 string.
2. `Image.reduceResolution: input does not have a valid default projection`
   -- `ImageCollection.mosaic()` doesn't carry scale/projection metadata;
   needs an explicit `.setDefaultProjection()` from one source image.
3. `Image.clipToBoundsAndScale: geometry for image clipping must be bounded`
   -- download/thumbnail generation needs an explicit bounded region.
4. `Total request size (X bytes) must be <= 50331648 bytes` -- the
   synchronous download 48 MiB cap.
5. `Output of image computation is too large (X MiB > 80.0 MiB)` -- a
   second, separate internal computation cap, hit even after chunking for
   (4).
6. The `2^31` pixel ceiling above -- the real, structural limit.

## Unrelated auth gotchas hit along the way (would recur if Earth Engine is
used again for anything in this project)

- A brand-new Earth Engine project can take 10-60 minutes to propagate after
  registration; `"OAuth client is not fully created yet"` and
  `"Asset ... does not exist"` errors can resolve themselves with no code
  changes after waiting.
- The default `ee.Authenticate()` scope list requests `drive` and
  `devstorage.full_control`, which can produce
  `RefreshError: invalid_scope` on a fresh project. Authenticate with only
  the scopes actually needed
  (`earthengine` and `cloud-platform`).
- Google Cloud Console's "Asset Inventory" is a different product from the
  Earth Engine Code Editor's own "Assets" tab; use
  `code.earthengine.google.com` to check Earth Engine assets, not
  `console.cloud.google.com`.
