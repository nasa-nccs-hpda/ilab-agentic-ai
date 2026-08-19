# ILAB Agentic AI

ILAB Agentic AI is a shared repository for project knowledge, reusable agent skills, agent configurations, integrations, examples, and evaluations used across ILAB teams.

The repository is designed for two equally important kinds of contribution:

1. Capture useful information where a project team can find it.
2. Promote proven, reusable material into shared knowledge or agent capabilities.

You do not need to create a skill to contribute. Project notes, dataset descriptions, model runbooks, troubleshooting guidance, prompts, and examples are all valuable.

## Start here

- Working on a specific effort? Begin in [`projects/`](projects/README.md).
- Adding scientific or technical information used by several projects? Use [`knowledge/`](knowledge/README.md).
- Teaching an agent a repeatable procedure? Use [`skills/`](skills/README.md).
- Defining a reusable agent role? Use [`agents/`](agents/README.md).
- Documenting Mantle, Slurm, GitHub, MCP, or another external system? Use [`integrations/`](integrations/README.md).
- Proving that something works? Add an evaluation under [`evals/`](evals/README.md).
- Unsure where to begin? Read [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Repository model

```text
Project note -> Shared knowledge -> Repeatable skill -> Evaluated capability
```

| Area | Purpose | Example |
| --- | --- | --- |
| `projects/` | Project-owned context and working material | IMVI datasets, terminology, examples |
| `knowledge/` | Information reused across projects | Landsat, hyperspectral sensors, model descriptions |
| `skills/` | Small, repeatable actions for agents | Preprocess imagery, submit Slurm jobs |
| `agents/` | Roles composed from skills and context | Scientist, model operator, reviewer |
| `integrations/` | External platforms and services | NASA Mantle, Slurm, GitHub |
| `evals/` | Tests and evidence for agent behavior | Skill scenarios, expected outputs |
| `templates/` | Starting points for new contributions | Project, knowledge entry, skill |
| `tools/` | Utilities for maintaining this repository | Validation and catalog generation |

## First project

[`projects/imvi/`](projects/imvi/README.md) is the initial project workspace. Its contents may remain IMVI-specific until another project needs them. Shared material can then be promoted without losing attribution or ownership.

## Existing guides

- [NASA Mantle local LLM resources](docs/NASA-Mantle-LLM-Resources.md)
- [AI usage and token-saving strategies](docs/TokenSavingStrategies.md)

## Contribution principles

- Put information where its users will look for it.
- Start project-specific; generalize only when reuse is demonstrated.
- Prefer small, focused contributions over large catch-all documents.
- State ownership, sources, limitations, and review dates.
- Never commit credentials, tokens, proprietary data, or restricted information.
