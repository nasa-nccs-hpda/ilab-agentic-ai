# Troubleshooting: a crashed checkpoint write masqueraded as a completed one

## Symptom

A long-running, checkpointed per-tile evaluation loop crashed with
`NameError: name 'json' is not defined` partway through (an unrelated
kernel-state issue -- a module imported in an earlier cell hadn't actually
been re-run in the current kernel session). After fixing that and
re-running, the very next attempt crashed differently:

```text
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

on a file that the resume logic believed was a valid, already-completed
checkpoint for one tile.

## Confirmed cause

The checkpoint-save code was:

```python
with open(metrics_path, "w") as f:
    json.dump(m, f)
```

Opening a file in `"w"` mode **truncates it to empty immediately**, before
any data is written -- the actual content only lands once `json.dump()`
completes. Since `json.dump()` was the exact line that crashed (with
`json` undefined), the file had already been created and emptied by
`open()`, but never received any content. That left a genuine, real,
0-byte file sitting at the checkpoint path.

On the next run, the resume logic's `if metrics_path.exists(): ... continue`
check saw a file that existed and assumed it was a completed checkpoint --
because *existence* was the only thing being checked, not validity. Trying
to `json.load()` an empty file fails with the classic
"Expecting value: line 1 column 1" error, since there's nothing to parse.

## Resolution

Two independent fixes, addressing both directions of the problem:

**1. Write atomically**, so a crash mid-write can never leave a corrupt
file at the real checkpoint path:

```python
tmp_path = metrics_path.with_suffix(".json.tmp")
with open(tmp_path, "w") as f:
    json.dump(m, f)
os.replace(tmp_path, metrics_path)   # atomic on the same filesystem
```

A crash now leaves a stray `.tmp` file (harmless -- the resume logic never
looks for it) instead of a corrupt file at the path the resume logic
trusts.

**2. Treat a cache-read failure as "not actually cached," not a fatal
error** -- defends against any other cause of a corrupt/incomplete
checkpoint file, not just this specific crash:

```python
if metrics_path.exists():
    try:
        with open(metrics_path) as f:
            m = json.load(f)
        # ... use cached result, continue to next tile ...
        continue
    except (json.JSONDecodeError, KeyError):
        logger.warning(f"cached file corrupt/incomplete, re-extracting")
        # fall through and re-extract this tile below
```

## General lesson

For any resumable/checkpointed loop: **existence of a file is not the same
as validity of a file.** `open(path, "w")` creates/truncates on open, not on
write completion, so any code path that can fail between opening a file for
writing and finishing the write leaves a real, existing, but garbage file
behind -- and a naive `if path.exists(): skip` resume check will treat that
garbage as done. The fix is two-layered: write new checkpoints atomically
(temp file + rename) so this can't happen going forward, and make the
resume-read path tolerant of corrupt files it might still encounter (from
before the fix, or from any other partial-write cause) rather than trusting
existence alone.
