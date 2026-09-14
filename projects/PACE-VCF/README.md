# PACE-VCF

PACE-VCF asks whether PACE-OCI hyperspectral surface reflectance can produce
a Vegetation Continuous Fields (VCF) product -- percent tree cover, percent
non-tree vegetation, percent non-vegetated -- competitive with the existing
MODIS VCF (MOD44B) methodology, and whether foundation-model embeddings
(AlphaEarth) or deep-learning architectures (Spatial-CNN, Pixel-Transformer)
add value beyond a gradient-boosted-tree baseline built on hand-engineered
spectral indices.

**Status:** shelved for write-up. The pipeline runs end-to-end (raw PACE/VIIRS
downloads through metrics generation, training, inference, and a three-model
comparison), several real bugs found during development are fixed and
documented, and results are being summarized into a paper. This directory is
the durable record of what was built, what was tried and abandoned, and what
would need attention before the work resumes.

Working code lives in a private repository
(`github.com/nasa-nccs-hpda/PACE_VCF`) and an active working copy on NCCS
Explore; this project directory holds the knowledge, troubleshooting record,
and a curated, output-stripped set of representative notebooks -- not the
full working pipeline (which depends on internal `/explore/nobackup/...`
paths and restricted datasets).

## Where to look

- `knowledge/overview/` -- project goals, the experiment roadmap, final
  status, and how data flows through the pipeline.
- `knowledge/datasets/` -- PACE-OCI, VIIRS LST, MODIS VCF reference data, and
  AlphaEarth Foundations embeddings: what each is, how it's used, and its
  limitations.
- `knowledge/algorithms/` -- the phenology-based (AltSort) metric-sorting
  scheme, Int16 scaling/NaN-handling conventions, and the two-R²-definitions
  gotcha that affects every model-comparison result in this project.
- `knowledge/models/` -- XGBoost + Monte Carlo feature selection
  configuration, and the three-model (XGBoost / Spatial-CNN /
  Pixel-Transformer) comparison methodology and results.
- `knowledge/troubleshooting/` -- real bugs found during development, each
  with symptom, confirmed cause, and resolution. Several of these silently
  produced wrong metrics or optimistic scores rather than throwing errors --
  read this before trusting any historical number from this project that
  predates the listed fix.
- `examples/notebooks/` -- a curated, output-stripped set of notebooks
  representative of the final workflow (metrics generation, both training
  families, the three-model comparison, and inference). These will not run
  as-is outside the NCCS Explore environment; they document methodology and
  code structure, not a runnable pipeline.

## Owners

- Melanie Frost

## Contributing

- Project-specific context belongs in `knowledge/`; promote it to the
  repository's top-level `knowledge/` only if another project needs the same
  material (e.g. the AltSort phenology rationale or the two-R²-definitions
  note are general enough that a future hyperspectral VCF-style project could
  reuse them as-is).
- Do not add restricted data, credentials, or paths that assume access to
  NCCS-internal systems as if they were public.
- See `AGENTS.md` for agent-specific instructions when working in this
  directory.
