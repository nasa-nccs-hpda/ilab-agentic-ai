# Skills

Skills teach an agent how to perform a focused, repeatable task. They are not general topic folders or substitutes for project documentation.

Good names describe an action:

- `analyze-hyperspectral-imagery`
- `process-landsat-time-series`
- `build-dems-with-asp`
- `submit-slurm-jobs`
- `validate-model-output`

Avoid broad names such as `python`, `remote-sensing`, or `hpc` unless the intended behavior is genuinely narrow and clear.

## Skill contract

```text
<skill-name>/
├── SKILL.md              # required
├── agents/openai.yaml    # recommended
├── scripts/              # optional executable helpers
├── references/           # optional detailed knowledge
└── assets/               # optional output resources
```

Use `templates/skill/example-skill/` as a structural example. Actual skills should be initialized and validated with the current Codex skill tooling. Include optional directories only when required, and keep each skill self-contained.
