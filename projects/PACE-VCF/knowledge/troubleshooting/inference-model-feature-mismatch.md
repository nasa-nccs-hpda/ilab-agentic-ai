# Troubleshooting: inference silently used the wrong feature list

## Symptom

An inference run produced predictions that looked plausible (valid range,
reasonable spatial pattern) but were wrong -- the model had actually been
fed features in the wrong order/set relative to what it was trained on. No
exception was raised.

## Confirmed cause

Each trained model is saved alongside a companion "top features" text file,
matched by a shared timestamp in both filenames (e.g.
`pace_vcf_mc_xgb_<timestamp>.json` and `mc_top_features_<timestamp>.txt`).
The inference notebook derived the timestamp from the model filename with
`MODEL_PATH.stem.split('_')[-1]`, which only captures the *time* portion of
a `..._{date}_{time}` stem (e.g. `"164839"` instead of the full
`"20260831_164839"`). This made the companion-file lookup fail every time --
but the failure was masked by a silent fallback: if the exact companion file
wasn't found, the code picked whichever `mc_top_features_*.txt` was most
recently modified in the directory. That "worked" (no crash, no missing
data) right up until a second, differently-featured model run also landed in
the same output directory -- at which point inference silently paired one
model with another model's feature list.

## Resolution

- Fixed the timestamp extraction:
  `MODEL_PATH.stem.replace('pace_vcf_mc_xgb_', '')` (keeps the full
  `date_time` string).
- Removed the silent fallback entirely. If the exact companion file isn't
  found, the notebook now raises `FileNotFoundError` rather than guessing.

## Why this class of bug is worth flagging generally

A silent "best guess" fallback for a required, uniquely-identifying
artifact (a feature list that must match its exact model) converts a
loud, obvious failure (file not found) into a quiet, wrong one (file
found, just the wrong one). Prefer failing loudly when an artifact lookup
has no valid degraded mode.
