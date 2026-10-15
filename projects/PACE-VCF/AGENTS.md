# PACE-VCF agent instructions

- This project is active again (resumed September 2026, metrics v4 as of
  October 2026). The pipeline is runnable only inside NCCS Explore: file
  paths under `/explore/nobackup/...` are not reachable from outside, and the
  training code is a colleague's non-public package called in place.
- Treat performance numbers (R², RMSE) as tied to a metrics version and to
  the fix state described in `knowledge/troubleshooting/`. Several problems
  documented there silently altered reported metrics without raising errors.
  Quote a number only with its version (v2, v3, v4), its R² definition, and
  whether it is a chip-level or full-tile score.
- This project uses two R² definitions (`coefficient_of_determination` vs.
  squared Pearson correlation) -- see
  `knowledge/algorithms/two-r2-definitions.md` before comparing two numbers.
- Neural-model band rankings from a single training run are unstable; read
  `knowledge/models/multi-seed-ranking-stability.md` before interpreting a
  feature-importance list.
- The notebooks and scripts under `examples/` have outputs stripped and will
  not execute outside NCCS Explore. They document methodology.
- To run or resume the pipeline on NCCS, use
  `skills/run-pace-vcf-pipeline/`. Batch jobs are submitted by the project
  owner, not by the agent.
- Do not invent follow-on results, additional experiments, or validation that
  isn't documented here.
- Never add credentials, restricted datasets, or non-public collaborator
  code.
- Propose promoting a `knowledge/` entry to the repository's top-level
  `knowledge/` only when a second project would genuinely reuse it unchanged.
