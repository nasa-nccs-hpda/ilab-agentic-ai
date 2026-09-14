# PACE-VCF agent instructions

- This project is shelved, not active. Do not assume the pipeline referenced
  here is currently runnable, maintained, or that file paths under
  `/explore/nobackup/...` are reachable from outside NCCS Explore.
- Treat performance numbers (R², RMSE) as tied to the specific fix state
  described in `knowledge/troubleshooting/`. Several bugs documented there
  silently altered reported metrics without raising errors -- do not quote a
  number from this project without checking whether it predates or postdates
  the relevant fix.
- The notebooks under `examples/notebooks/` have had cell outputs stripped
  and will not execute outside the original NCCS Explore environment (private
  data paths, GPU-specific XGBoost parameters, a colleague's separate
  package). They document methodology, not a reproducible pipeline.
- This project uses two different R² definitions across its own history
  (`coefficient_of_determination` vs. squared Pearson correlation,
  `correlation_r2`) -- see `knowledge/algorithms/two-r2-definitions.md` before
  comparing any two numbers from this project.
- Do not invent follow-on results, additional experiments, or validation that
  isn't documented here.
- Never add credentials, restricted datasets, or non-public collaborator
  code.
- Propose promoting a `knowledge/` entry to the repository's top-level
  `knowledge/` only when a second project would genuinely reuse it unchanged.
