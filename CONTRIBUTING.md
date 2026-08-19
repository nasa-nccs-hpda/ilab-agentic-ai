# Contributing

Contributions can be as small as a corrected link or as substantial as a tested agent skill. The best starting location depends on what you are adding.

## Choose the contribution type

| You want to add | Start here |
| --- | --- |
| Information useful to one project | `projects/<project>/knowledge/` |
| A dataset, sensor, mission, model, or algorithm used by several projects | `knowledge/` |
| A repeatable procedure an agent should follow | `skills/` |
| A reusable agent role or configuration | `agents/` |
| Instructions for an external platform or service | `integrations/` |
| A prompt used only by one project | `projects/<project>/prompts/` |
| A test case or expected outcome | `evals/` or `projects/<project>/evals/` |

If you are uncertain, put the contribution under the project that needs it. Maintainers can promote it later.

## Basic workflow

1. Search the repository for an existing entry before creating one.
2. Copy the closest template from `templates/`.
3. Use lowercase, hyphen-separated directory names.
4. Fill in ownership, status, sources, and review information.
5. Add links from the nearest `README.md` when appropriate.
6. Check that examples contain no secrets or restricted data.
7. Open a pull request explaining who uses the contribution and how it was verified.

## Contribution lifecycle

New knowledge usually begins close to the people using it:

```text
projects/imvi/knowledge/datasets/example.md
    -> knowledge/datasets/example.md
    -> skills/earth-observation/process-example-data/
    -> evals/skills/process-example-data/
```

Promotion is appropriate when a second project needs the material, the procedure has stabilized, or automation would prevent repeated mistakes.

## Documentation standards

- Write for someone who is familiar with the field but new to the project.
- Explain acronyms on first use.
- Separate observed facts from recommendations or assumptions.
- Link to authoritative sources when possible.
- Record limitations, access restrictions, and known failure modes.
- Use examples with synthetic, public, or explicitly approved data.
- Prefer one focused page over one very large reference document.

## Skill standards

Every actual skill is a self-contained directory whose name matches the skill name:

```text
skills/<category>/<skill-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/       # only when needed
├── references/    # only when needed
└── assets/        # only when needed
```

Skill names must use lowercase letters, digits, and hyphens. Prefer verb-led names such as `analyze-hyperspectral-imagery` or `submit-slurm-jobs`.

`SKILL.md` frontmatter must contain only `name` and `description`. Put both what the skill does and when it should trigger in the description. Keep detailed domain material in `references/`, and include resource directories only when the skill actually needs them.

Scripts included in a skill must be run against a representative input before review. Include evaluation cases for fragile, safety-sensitive, or complex behavior.

## Pull request checklist

- [ ] The contribution is in the narrowest sensible location.
- [ ] Names are lowercase and hyphen-separated.
- [ ] Owners and sources are identified where applicable.
- [ ] Links and commands have been checked.
- [ ] Examples do not contain credentials or restricted information.
- [ ] Scripts or procedures were tested, or the PR explains why they were not.
- [ ] Shared content does not unnecessarily duplicate project content.
