---
title: One seed controlled both the data split and the model start
owners:
  - Melanie Frost
projects:
  - pace-vcf
status: draft
last-reviewed: 2026-10-15
---

# Troubleshooting: one seed controlled both the data split and the model start

## Symptom

Found before it caused a wrong result. To measure run-to-run variation, the
plan was to retrain the neural chip models with different `--seed` values.
Reading the training code showed that this would also have changed which
chips were in train, validation and test -- so seed-to-seed differences
would have mixed model randomness with a different test set.

## Confirmed cause

In the colleague's neural training command (`pace_vcf_toy.train`), the single
`--seed` argument sets both the chip split (`SplitConfig(seed=...)`) and the
model's random start (`LightningRunOptions(seed=...)`, which calls
`pl.seed_everything`). The XGBoost command does not have this problem: it has
separate `--split-seed` and `--seed`.

## Resolution

A small wrapper (`train_init_seed.py`, see `examples/scripts/`) builds the
experiment configuration exactly as the colleague's command does -- split
seed from `--seed 7` -- and passes a separate `--init-seed` to the Lightning
runner. The colleague's package is imported unchanged. Each run logs
`split seed 7 | model init seed N` and writes `seeds.json`; `--init-seed`
equal to `--seed` reproduces the original command exactly.

## General lesson

Before using "different seeds" to measure variability, check what each seed
controls. A seed that also drives the data split turns a model-variance
study into a data-variance study, and makes test scores incomparable.
