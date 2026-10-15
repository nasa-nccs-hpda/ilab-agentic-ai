# PACE-VCF

PACE-VCF asks whether PACE-OCI hyperspectral surface reflectance can produce
a Vegetation Continuous Fields (VCF) product -- percent tree cover, percent
non-tree vegetation, percent non-vegetated -- competitive with the existing
MODIS VCF (MOD44B) methodology, and whether foundation-model embeddings
(AlphaEarth) or deep-learning architectures (Spatial-CNN, Pixel-Transformer)
add value beyond a gradient-boosted-tree baseline built on hand-engineered
spectral indices.

**Status:** active. The project was shelved for write-up, then resumed in
September/October 2026 to fix the input metrics and redo the model comparison
on them. The current state is **metrics v4** (October 2026): the
metrics were corrected (v3) and then de-duplicated and redefined to their
original intent (v4), and the three chip models were retrained, checked for
seed sensitivity, and run globally on all 291 MODIS-VCF land tiles. Results
in this directory are the v4 results unless a page says otherwise; the
shelved-era (v2) numbers are kept where they explain history and are marked
as such.

Working code lives in a private repository
(`github.com/nasa-nccs-hpda/PACE_VCF`) and an active working copy on NCCS
Explore; this project directory holds the knowledge, troubleshooting record,
a run-book skill, and curated, output-stripped notebooks and scripts -- not
a runnable pipeline (it depends on internal `/explore/nobackup/...` paths,
restricted datasets, and a colleague's non-public training package).

## How the work was done

The work began with a chat assistant (code and questions pasted into a
chatbot, answers pasted back). Around the end of metrics v2 and the start of
v3 it moved to **agentic Claude (Claude Code) inside VS Code** on NCCS
Explore: the agent read and edited the project files directly, wrote and
dry-ran the batch launchers, watched jobs, scored results, and kept the
project log, while the project owner submitted every batch job, made the
scientific decisions, and reviewed the results. What that changed, and where
it fell short, is in `knowledge/overview/agentic-workflow.md`.

## Where to look

- `knowledge/overview/` -- project goals, the experiment roadmap and status,
  how data flows through the pipeline, and how the agentic workflow was used.
- `knowledge/datasets/` -- PACE-OCI, VIIRS LST, MODIS VCF reference data, and
  AlphaEarth Foundations embeddings.
- `knowledge/algorithms/` -- the phenology-based (AltSort) metric sorting,
  Int16 scaling and NaN conventions, the v4 metric definitions and
  duplicate-band removal, and the two-R²-definitions gotcha.
- `knowledge/models/` -- XGBoost + Monte Carlo feature selection, the
  three-model (XGBoost / Spatial-CNN / Pixel-Transformer) comparison, the
  band-count sweep, the multi-seed ranking-stability study, and what the
  PACE-derived bands add over MODIS-equivalent ones.
- `knowledge/troubleshooting/` -- real problems found during development,
  each with symptom, confirmed cause, and resolution. Several silently
  produced wrong or optimistic numbers rather than errors -- read this
  before trusting any historical number from this project.
- `skills/run-pace-vcf-pipeline/` -- how an agent runs, checks and resumes
  the pipeline on NCCS (internal to NCCS; not runnable elsewhere).
- `examples/notebooks/` and `examples/scripts/` -- curated, output-stripped
  notebooks and the batch launchers used for v4. They document methodology;
  they will not run outside NCCS Explore.

## Owners

- Melanie Frost

## Contributing

- Project-specific context belongs in `knowledge/`; promote it to the
  repository's top-level `knowledge/` only if another project needs the same
  material (e.g. the AltSort phenology rationale, the two-R²-definitions
  note, or the multi-seed ranking-stability method).
- Do not add restricted data, credentials, or paths that assume access to
  NCCS-internal systems as if they were public.
- See `AGENTS.md` for agent-specific instructions when working in this
  directory.
