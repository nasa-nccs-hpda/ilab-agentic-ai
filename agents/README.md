# Agents

Agent entries define reusable roles by composing skills, knowledge, integrations, and operating constraints. Keep agent definitions small; do not copy entire domain references into agent prompts.

Examples might include a scientific analyst, model operator, software engineer, or reviewer. Project-specific agents belong under `projects/<project>/agents/` until they are useful elsewhere.

An agent entry should state:

- its purpose and boundaries
- its owners
- the skills and knowledge it uses
- the tools or integrations it requires
- its safety and information-handling constraints
- the evaluations that demonstrate expected behavior

Start with `templates/agent/`.
