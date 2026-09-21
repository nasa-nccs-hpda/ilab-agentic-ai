# Troubleshooting: GPU XGBoost training failed twice, for two unrelated reasons

## Symptom 1: `tree_method="gpu_hist"` rejected outright

```text
XGBoostError: Invalid Input: 'gpu_hist', valid values are: {'approx', 'auto', 'exact', 'hist'}
```

## Confirmed cause 1

`gpu_hist` was XGBoost's GPU tree-method string in the 1.x API. XGBoost
2.0+ removed it: GPU selection is now a separate `device` parameter
combined with `tree_method="hist"`, not a distinct tree-method value. The
kernel in use had a newer (2.0+) XGBoost than whatever environment this
project's other training notebooks (`6h`, `6g`, etc. -- all still using
`tree_method: 'gpu_hist'` in their `XGB_PARAMS`) were originally run under.
Those notebooks would hit the same error if run in *this* kernel.

## Resolution 1

```python
# old (XGBoost 1.x): tree_method="gpu_hist"
# new (XGBoost 2.0+): tree_method="hist", device="cuda"
model = xgb.XGBRegressor(tree_method="hist", device="cuda", ...)
```

## Symptom 2: a different error after fixing the first one

```text
XGBoostError: This program was not compiled for SM 70
: cudaErrorInvalidDevice: invalid device ordinal
```

## Confirmed cause 2

A completely different problem, only visible after fixing symptom 1: **the
GPU hardware itself.** "SM 70" is NVIDIA's compute-capability label for the
Volta architecture (e.g. Tesla V100). The `xgboost` package had been
installed via a plain `pip install xgboost` (see
`knowledge/troubleshooting/` -- this project's earlier `--user`-install
environment-contamination issue traces back to the same install). The
resulting prebuilt PyPI wheel's GPU kernels were compiled for a different,
newer set of compute architectures and simply don't include SM 70 at all --
this isn't a configuration mistake, the installed binary is incapable of
running on this GPU regardless of how it's invoked.

## Resolution 2

Fell back to CPU rather than chasing a differently-compiled GPU build:

```python
model = xgb.XGBRegressor(tree_method="hist", ...)   # no device= at all
```

Deliberately **not** attempting to install a custom-compiled xgboost with
broader GPU architecture support -- this project's environment has already
been destabilized once by an unpinned `pip install` affecting a different,
unrelated kernel (see the `pip install --user` troubleshooting entry). CPU
`hist` was sufficient at this training set's scale (a few million rows after
the per-tile subsampling cap).

## General lesson

A GPU-related XGBoost failure can be a **software API mismatch**
(`tree_method` naming changed between major versions -- fixable by updating
the call) or a **hardware/binary mismatch** (the installed build simply
doesn't support the physical GPU present -- not fixable by changing
parameters, only by installing a differently-compiled package, which on a
shared/fragile environment may not be worth the risk). The two produce
different-looking errors and require different fixes; don't assume fixing
one means GPU training is unblocked -- check that training actually
proceeds, not just that the first error went away.
