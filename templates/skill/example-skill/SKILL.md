---
name: example-skill
description: Demonstrate the required structure of an ILAB agent skill. Use when a contributor needs a copyable example for creating a focused, self-contained skill with optional references and scripts.
---

# Example skill

Use this directory as a structural example. Rename the directory and replace all example content when creating an actual skill.

## Workflow

1. Confirm the requested outcome and required inputs.
2. Read `references/example-reference.md` only when the example domain detail is needed.
3. Run or adapt `scripts/example_check.sh` only when a deterministic check is useful.
4. Report the result, assumptions, and any validation performed.

## Requirements

- Keep the skill focused on one repeatable outcome.
- Include only non-obvious instructions the agent needs.
- Test included scripts against representative inputs.
- Remove optional files and directories that the real skill does not use.
