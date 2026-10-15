---
title: Slurm array tasks killed when the last task finished
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: Slurm array tasks killed when the last task finished

## Symptom

Multi-task Slurm job arrays on NCCS Explore lost tasks partway through: some
array tasks ended with exit `0:9` (SIGKILL) and no out-of-memory or time-limit
message, leaving their tiles unfinished. Observed three times (2026-09-30
once, 2026-10-09 twice) on chip-building and stack-building arrays.

## Confirmed cause

Partly confirmed. The killed tasks were running on the same node as other
tasks of the same array, and they were killed at the moment the array's
highest-index task finished. The underlying scheduler or node-cleanup
behaviour was not identified, and the pattern was not reported to NCCS at
the time of writing.

## Resolution

Stopped using multi-task job arrays for multi-tile work. Instead:

- several **independent** jobs, each with its own tile list, or
- one job (or a one-task array) that loops over a tile-list file.

No task has been lost since. Launchers make the work resumable (finished
tiles are skipped), so a relaunch only redoes what is missing.

## General lesson

When batch tasks die with SIGKILL and no resource message, check whether
they shared a node and when they died relative to sibling tasks. Make
multi-item batch work resumable so a lost task costs a relaunch, not a
rebuild.
