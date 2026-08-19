# Repository instructions for agents

## Purpose

Treat this repository as a shared agent platform and institutional knowledge base. Preserve the distinction between project-local material and reusable components.

## Placement rules

- Put new, project-specific information in `projects/<project>/`.
- Put information reused by multiple projects in `knowledge/`.
- Put repeatable agent procedures in `skills/`.
- Put reusable role configurations in `agents/`.
- Put external service and platform instructions in `integrations/`.
- Put behavioral verification in `evals/`.

When placement is unclear, prefer the relevant project directory. Do not generalize speculative or project-specific practices into shared guidance.

## Editing rules

- Preserve owners, sources, limitations, and review dates.
- Do not invent project facts, model behavior, dataset characteristics, or validation results.
- Never add secrets, credentials, restricted data, or production endpoints without explicit authorization.
- Use lowercase, hyphen-separated directory names.
- Keep skills small, task-oriented, and self-contained.
- Validate scripts and links in proportion to their risk.
- Remove `.gitkeep` when a directory gains real content.
