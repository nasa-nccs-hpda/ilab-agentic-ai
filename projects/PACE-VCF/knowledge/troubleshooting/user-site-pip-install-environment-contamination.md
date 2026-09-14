# Troubleshooting: `pip install --user` broke a different, unrelated kernel

## Symptom

A Jupyter kernel that had been working correctly for months suddenly failed
with `ImportError: sklearn needs to be installed in order to use this
module` when constructing an `xgboost.XGBRegressor` -- in a kernel that had
never been touched, immediately after an unrelated `pip install xgboost` was
run to fix a *different* kernel's missing-xgboost problem.

## Confirmed cause

`pip install xgboost` (run without an active, correctly-activated virtual
environment) defaulted to a `--user` install, landing in
`~/.local/lib/python3.12/site-packages/`. A `--user` install is **not**
scoped to one conda environment or one kernel -- it's visible to *every*
Python interpreter under that account with a matching version, whether that
interpreter is a "real" isolated environment, a shared HPC "prod" install,
or (for container-based kernels) any container that bind-mounts `/home`.

The newly pip-installed xgboost pulled in a newer version than whatever the
previously-working kernel had, and that newer xgboost requires
`scikit-learn` as an explicit dependency -- which was present for the
kernel's own original xgboost but not for the shadowing user-site one.

A second, related discovery: a Jupyter kernel that had been registered
earlier under a name suggesting an isolated environment
(`"pace-vcf (colleague env)"`) turned out, on inspection of its
`kernel.json`, to actually point at a shared "prod" JupyterLab Python
interpreter -- because the `conda activate` step silently failed (broken
`conda` in that shell) when the kernel was registered, so
`python -m ipykernel install` captured whatever `python`/`pip` were already
first on `PATH` instead of the intended isolated environment.

## Resolution

`pip install --user scikit-learn` (additive; restores the missing
dependency for the newer xgboost without removing anything already
working). Confirmed the fix from the traceback path itself
(`~/.local/lib/python3.12/site-packages/xgboost/core.py` in the error --
proof the import was resolving to the user-site copy, not any
environment-specific one).

## General lesson

On a shared HPC system with multiple Jupyter kernels, `pip install` without
an explicitly and correctly activated environment is a shared-state mutation
across *all* kernels that share that Python version and user account, not a
change scoped to the kernel you were looking at when you ran it. Before
running any bare `pip install` to fix a kernel problem:
- Confirm which interpreter is actually active
  (`import sys; print(sys.executable)` as a notebook cell is the reliable
  check -- kernel *display names* can be misleading, as above).
- Prefer a real, isolated environment (conda env, venv) over a `--user`
  install when multiple kernels on the same system need different package
  versions.
