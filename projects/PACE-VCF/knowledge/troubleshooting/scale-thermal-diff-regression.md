# Troubleshooting: two thermal-difference metrics always 0% valid

## Symptom

`AmpBandRefl-Band31` and `ThermalGreenBrownDiff-Band31` are 0% valid pixels
in every tile, every time -- not a per-tile data gap. Confirmed across all
test tiles. The underlying signal is genuinely computable: an independently
generated chip training dataset (a colleague's separate pipeline) has these
same two bands at ~100% valid, confirming this project's own metrics
notebooks were mishandling the scaling, not missing real data.

## Confirmed cause

Both bands are temperature *differences* (`AmpBandRefl-Band31` = max-min;
`ThermalGreenBrownDiff-Band31` = greenest3-minus-brownest3), but were being
scaled with `scale_thermal()`, which gates validity on `200 < data < 400`
(i.e. it only accepts absolute Kelvin values). A difference of two
temperatures essentially never falls in that range, so every pixel fails
the check and gets set to `NO_DATA` -- silently, no exception raised. See
`knowledge/algorithms/scaling-conventions-and-nan-handling.md` for the
scaling functions involved.

## History (why this took a while to notice)

- Original metrics notebook: both bands broken via `scale_thermal()`.
- A later notebook, adding snow-aware handling: computation refined, but the
  same scaling bug remained.
- A subsequent notebook: a real fix landed -- a new `scale_thermal_diff()`
  function (same x100 scaling, no absolute-range gate), with both bands
  switched to use it.
- The next metrics notebook after that: **regression** -- both bands were
  reverted back to `scale_thermal()`, and `scale_thermal_diff()` wasn't even
  defined anymore. The notebook appears to have been branched from an
  earlier point in the notebook lineage than the one containing the fix,
  silently dropping it.
- Two training notebooks worked around the bug by excluding these two
  features from training entirely (`problematic_features` exclusion list)
  rather than by fixing the root cause.

## Resolution

A new metrics notebook re-applied the correct fix (re-adding
`scale_thermal_diff()`, switching both bands to use it) on top of the most
recent metrics-computation improvements, and became the canonical
metrics-generation notebook going forward. All existing metrics TIFs
generated before this fix need regeneration for these two bands to actually
contain data. The training-notebook exclusion of these two features was
removed once tiles were regenerated.

## How to catch this class of bug earlier

Run the per-band validity check from
`knowledge/algorithms/scaling-conventions-and-nan-handling.md` after
generating or regenerating any metrics file. A flat 0%-valid band, in every
tile, is a scaling/gating bug, not a data availability issue -- real data
gaps are partial and vary by tile/region.
