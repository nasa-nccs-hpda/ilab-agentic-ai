---
title: How an agentic assistant was used in PACE-VCF
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# How an agentic assistant was used in PACE-VCF

## Summary

The project started with a chat assistant: code and questions were pasted
into a chatbot and answers pasted back. The primary code was run in
successive versions of ADAPT JupyterHub sessions, and webpages, PDFs and
documents were uploaded to a file search for the custom agent. Around the
end of metrics v2 and the start of v3 (September 2026) it moved to
**agentic Claude (Claude Code) running inside VS Code** on NCCS Explore. From
then on the agent read and edited project files directly, wrote and dry-ran
batch launchers, watched jobs, scored and compared results, and kept the
project log. The workflow also moved from Jupyter notebooks to batch jobs
submitted from the `gpulogin1` node. The project owner submitted every batch
job, made every scientific and modelling decision, and reviewed the results.
This page records what that changed and where it fell short, from the v3/v4
work (September to mid-October 2026).

## How the work was divided

| The agent did | The project owner did |
| --- | --- |
| Read code and outputs, found inconsistencies | Decided what the metrics should mean (e.g. "use the original intent of the amplitude and median metrics") |
| Wrote metric code, launchers, checks, notebooks | Pointed to authoritative sources (a colleague's current code branch) |
| Dry-ran every launcher with a fake `sbatch` before submission | Reviewed edits before they were written; submitted all batch jobs (`sbatch` is only available on the GPU login node, not in the agent's shell) |
| Watched jobs, combined and scored results as they landed | Chose band counts, the consensus approach, and which final model to keep |
| Kept the project README (status, decisions with dates, daily log) | Reviewed results and corrected the agent |

## What the agentic workflow added in v3 and v4

Confirmed from the project log:

- **Problems found by checking every output against what it should be.**
  100 of the 521 v2/v3 bands were exact copies of other bands; the MODIS VCF
  reference code's "median greenness" metrics run a plain median; the chip
  training package's command uses one seed for both the chip split and the
  model initialisation; full-tile scoring was swamped by median-filled no-data
  pixels; a final model scored 0.7 RMSE worse than expected. None needed
  insight so much as systematic checking, which is tedious by hand and cheap
  for an agent. Each is written up under `knowledge/troubleshooting/` or
  `knowledge/algorithms/`.
- **Noise measured instead of assumed.** A multi-seed study turned "the
  neural rankings look unstable" into numbers, showed that a CNN accuracy
  drop between metric versions was within run-to-run noise, and showed that
  a poor final model was an unlucky draw rather than a bad band list.
- **Speed made safe.** Every launcher refuses to overwrite earlier runs or
  write into a colleague's directory, neural jobs refuse to run without a
  GPU, and every launcher was dry-run with a fake `sbatch` before the owner
  submitted it -- which caught several bugs in the agent's own scripts
  before they reached the queue. v4 went from new metric definitions to
  global maps in about two and a half days, mostly batch time.
- **Documentation as a by-product.** Decisions were recorded with who and
  when; the metrics were put in a notebook for repeatability; the method was
  captured as a skill (`skills/run-pace-vcf-pipeline/`); this knowledge
  directory was drafted from that record.

## Where it fell short

- **Confident errors.** The agent attributed a coverage gain to the wrong
  cause, overstated which bands were duplicates, described run-to-run
  variation that did not exist, ran a neural scoring job on a login-node CPU
  before being told not to, once put a placeholder into a command the owner
  then ran, and took fill values as regular values instead of NaN. The owner
  caught most of these; review remains essential.
- **Volume.** The agent produces many tables and caveats; the one that
  matters is easy to miss.
- **Context between sessions.** Long sessions are summarised and new ones
  start cold; the project README and a short memory note mitigated this, but
  a resumed session can work from stale assumptions.
- **No job submission.** The agent prepares and verifies; a person submits.
  This adds a step, and is also a useful safety boundary on shared
  infrastructure.

## Practices worth reusing

- Keep one living project README (status line, decisions with dates, daily
  log) that the agent reads first and updates after every step.
- Ask the agent to dry-run launchers with a stub scheduler and to check every
  output (counts, band order, labels) before trusting it.
- Record standing rules as short, explained memory notes (e.g. "neural work
  on GPU batch nodes only", "ask before editing files").
- Quote every number with its metric version, R² definition, and whether it
  is chip-level or full-tile.

## Limitations and known issues

This is one project's experience with one agent and one owner; it is not a
controlled comparison with the chatbot phase. Time savings are estimates from
the project log, not measurements. Models were not fine-tuned; most of the
scientific work focused on the input metrics.

## Sources

- Project working README and daily log on NCCS Explore (internal).
- Melanie Frost (project owner).
