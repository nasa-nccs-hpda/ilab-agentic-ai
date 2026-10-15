---
title: GeoTIFF writes fail with "PROJ: proj_create_from_name"
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: GeoTIFF writes fail with "PROJ: proj_create_from_name"

## Symptom

With `gdal.UseExceptions()` enabled, writing a GeoTIFF failed with an error
of the form:

```text
PROJ: proj_create_from_name: Open of .../share/proj failed
```

It happened in a login shell and on batch nodes, but an earlier JupyterHub
notebook writing similar files had not hit it.

## Confirmed cause

Partly confirmed: GDAL could not open the PROJ database in the shared
environment's `share/proj` from those processes. Why the JupyterHub kernel
was unaffected was not identified. Stray `GDAL_DATA` / `GDAL_DRIVER_PATH`
values in the environment can also point GDAL at the wrong install.

## Resolution

- Unset `GDAL_DATA` and `GDAL_DRIVER_PATH` before running.
- Make a private copy of the environment's `share/proj` and point
  `PROJ_DATA` and `PROJ_LIB` at it before Python starts (the batch launchers
  test a write first and fall back to the copy, removing it on exit).
- In an already-running Python session, set
  `osr.SetPROJSearchPaths([path_to_copy])` -- environment variables set after
  GDAL has loaded are not picked up.

The shared environment itself was not changed.

## General lesson

When a geospatial write fails on PROJ only in some contexts, compare the
environment variables and the PROJ search path between the working and
failing contexts; fix it per process rather than editing a shared
installation.
