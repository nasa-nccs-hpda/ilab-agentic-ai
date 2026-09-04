# How to Add Agent Context to `ilab-agentic-ai`

This guide explains how to preserve useful information from ChatGPT, Claude, Codex, Copilot, or other AI-agent sessions so another agent—or the same agent in a new session—can continue the work without starting from scratch.

Repository:

`nasa-nccs-hpda/ilab-agentic-ai`

The repository is organized around a simple principle:

> Store durable project knowledge and agent instructions in Git, rather than relying on the lifetime of an individual chat session.

A chat session is temporary. The repository should contain the information needed to reconstruct the important state of the work.

---

# 1. Decide What You Are Saving

Before adding anything, determine what kind of information came out of the agent session.

Use this mapping:

| Information                                             | Store it under                |
| ------------------------------------------------------- | ----------------------------- |
| Context specific to one project                         | `projects/<project>/`         |
| Technical/scientific information useful across projects | `knowledge/`                  |
| A procedure an agent can repeat                         | `skills/`                     |
| A reusable agent role or configuration                  | `agents/`                     |
| Instructions for Mantle, SLURM, GitHub, MCP, APIs, etc. | `integrations/`               |
| Expected agent behavior or tests                        | `evals/`                      |
| Project-specific prompts                                | `projects/<project>/prompts/` |

When you are uncertain, **start under the project**. Shared information can be promoted later.

For example:

```text
projects/imvi/
```

may contain information specific to IMVI.

If several projects later need the same information, move or promote it into a shared location such as:

```text
knowledge/
skills/
agents/
integrations/
```

---

# 2. Do Not Store Entire Chat Transcripts

Do **not** copy a 100-message ChatGPT conversation into Git.

Chat transcripts typically contain:

* repeated questions
* incorrect intermediate answers
* abandoned approaches
* debugging noise
* conversational text
* information that is no longer current

Instead, extract the durable information.

A good session summary answers:

```text
What are we trying to accomplish?

What is already known?

What did we decide?

What changed?

What worked?

What did not work?

What remains unresolved?

What should the next agent do?
```

Think of this as converting:

```text
conversation
    ↓
compressed project state
    ↓
repository
```

---

# 3. Start From the Project Template

For a new project, copy:

```bash
cp -r templates/project projects/<project-name>
```

For example:

```bash
cp -r templates/project projects/satvision-pix4d
```

The repository project template currently contains:

```text
README.md
AGENTS.md
project.yaml
```

Every project should at minimum complete those files.

Project names should use lowercase and hyphens:

```text
satvision-pix4d
fire-hnl
earthcare-retrieval
geos-gpu
```

rather than:

```text
SatVision_PIX4D
Fire HNL
GEOS_GPU
```

---

# 4. Put Stable Project Context in `README.md`

The project README explains what the project is.

It should contain relatively stable information such as:

```markdown
# SatVision Pix4D

## Objective

Develop a foundation model for geostationary satellite imagery
using GOES ABI observations.

## Primary Tasks

- self-supervised pretraining
- cloud reconstruction
- convective-system identification
- nowcasting

## Data

GOES ABI L1b imagery.

## Infrastructure

Training is performed on NASA NCCS GPU systems.

## Owners

- <name>
- <name>

## Important Links

- Source repository:
- Documentation:
- Data location:
```

Avoid putting rapidly changing debugging status here.

---

# 5. Put Agent Instructions in `AGENTS.md`

`AGENTS.md` should tell an AI agent **how to behave when working on this project**.

For example:

````markdown
# Agent Instructions

## Before Starting Work

Read:

1. `README.md`
2. `project.yaml`
3. project knowledge
4. current status or handoff information
5. recent Git history

Before modifying code, inspect:

```bash
git status
git log --oneline -10
git diff
````

## Project Rules

* Do not modify raw datasets.
* Do not commit credentials.
* Prefer configuration files over hardcoded parameters.
* Preserve existing APIs unless explicitly asked to change them.
* Add tests when modifying production code.

## Scientific Rules

* Distinguish observed results from hypotheses.
* Do not invent citations.
* Record the provenance of scientific datasets.
* Record units, spatial resolution, temporal resolution, and coordinate systems.

## Before Ending a Session

Record:

* completed work
* files modified
* commands or evaluations performed
* unresolved problems
* important decisions
* exact recommended next step

````

This is the file that helps a new ChatGPT/Codex/Claude session understand **how it is expected to work**.

---

# 6. Preserve Session State

For substantial agent work, create a project-specific status or handoff document.

A useful layout is:

```text
projects/<project>/
├── README.md
├── AGENTS.md
├── project.yaml
├── knowledge/
├── prompts/
├── evals/
└── status/
    ├── current.md
    └── decisions.md
````

You do not need every directory for every project. Create only what the project actually uses.

## `status/current.md`

Use this for the current state of the work.

Example:

```markdown
# Current Status

Last updated: 2026-09-04

## Current Objective

Enable distributed training of the model.

## Working

- preprocessing pipeline
- dataset loader
- single-GPU training
- checkpoint loading
- two-GPU distributed training

## Current Problem

Training hangs when more than four GPUs are used.

The last visible message is:

`Initializing process group`

## Already Tried

- `NCCL_DEBUG=INFO`
- explicit `MASTER_ADDR`
- explicit `MASTER_PORT`

These did not resolve the issue.

## Next Step

Verify that every rank reaches:

`dist.init_process_group()`

Then inspect NCCL logs from an eight-GPU run.
```

This is far more useful than pasting the entire debugging conversation.

---

# 7. Record Important Decisions Separately

AI agents frequently revisit decisions when they do not know why something was chosen.

Keep important architectural or scientific decisions in something like:

```text
projects/<project>/status/decisions.md
```

Example:

```markdown
# Decisions

## 2026-09-02 — Keep time as an explicit tensor dimension

### Decision

Model input will use:

[B, T, C, H, W]

### Reason

Future architectures need to operate explicitly over time.

### Rejected Alternative

Flattening time and channels into:

[B, T*C, H, W]

### Consequence

Dataset loaders and augmentation functions must preserve the temporal dimension.
```

Another example:

```markdown
## 2026-09-03 — Use Zarr for training data

### Decision

Use Zarr for preprocessed training data.

### Reason

Random-access performance was better than reading the original
NetCDF files during training.

### Do Not Revisit Unless

Performance characteristics or storage requirements change.
```

This prevents agents from repeatedly proposing solutions the team already evaluated.

---

# 8. Store Project Knowledge Near the Project First

Suppose a ChatGPT session produces useful information about a project dataset.

Place it under:

```text
projects/<project>/knowledge/
```

For example:

```text
projects/imvi/knowledge/datasets/cpl.md
```

A useful dataset entry might contain:

```markdown
# CPL

## Description

Cloud Physics Lidar observations used by the project.

## Variables Used

- altitude
- backscatter
- cloud mask
- geolocation

## Coordinate System

Vertical coordinate: altitude above ...

## Known Issues

- missing observations on some flight days
- variable vertical sampling
- occasional fill values

## Project Usage

Used as the preferred lidar source when available.

Fallback:

ALICAT is used when CPL is unavailable.

## Source

<authoritative source>

## Last Reviewed

2026-09-04
```

If another project later needs the same CPL information, promote the durable portion to:

```text
knowledge/
```

and keep only project-specific details under the project.

---

# 9. Convert Repeatable Agent Work Into a Skill

If an agent performs the same procedure repeatedly, do not keep describing the procedure in prompts.

Create a skill.

The repository expects skills to follow this structure:

```text
skills/<category>/<skill-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
├── references/
└── assets/
```

Only create optional directories when they are needed.

Skill names should be lowercase and hyphenated, preferably verb-led.

Good examples:

```text
submit-slurm-jobs
analyze-hyperspectral-imagery
prepare-goes-training-data
validate-model-checkpoints
```

A skill should represent a repeatable procedure.

For example:

```markdown
---
name: submit-slurm-jobs
description: Submit and diagnose SLURM jobs on NASA NCCS systems when an agent needs to launch or troubleshoot HPC workloads.
---

# Submit SLURM Jobs

## Procedure

1. Inspect the requested resource requirements.
2. Validate partition and account.
3. Generate the SLURM script.
4. Submit with `sbatch`.
5. Record the returned job ID.
6. Inspect status with `squeue`.
7. If the job fails, inspect logs before modifying resource requests.

## Safety

Never delete another user's jobs.

Never expose credentials or tokens.

## References

See `references/nccs-slurm.md`.
```

The repository contribution guidelines specifically require actual skills to be self-contained directories with a `SKILL.md`, and skill names should use lowercase letters, digits, and hyphens.

---

# 10. Create an Agent Role Only When the Role Is Reusable

Not every prompt needs to become an agent.

Create something under:

```text
agents/
```

when you are defining a reusable role.

Examples:

```text
research-scientist
code-reviewer
model-operator
data-engineer
literature-reviewer
```

A project-specific instruction such as:

> Use CPL before ALICAT for the WH2yMSIE experiment.

probably belongs under the project.

A reusable instruction such as:

> Review scientific machine-learning code for numerical correctness, data leakage, reproducibility, and evaluation validity.

may belong in a reusable agent definition.

---

# 11. Store Prompts Only When They Are Actually Useful

Do not save every prompt anyone sends to ChatGPT.

Save prompts that:

* are repeatedly used
* encode useful project behavior
* have been tested
* consistently produce useful results
* contain non-obvious project instructions

Project-specific prompts belong under:

```text
projects/<project>/prompts/
```

For example:

```text
projects/geos-gpu/prompts/
├── translate-fortran-kernel.md
├── review-gpu-port.md
└── summarize-performance-results.md
```

---

# 12. Preserve Failures and Known Limitations

Agents benefit substantially from knowing what **not** to repeat.

Instead of writing only:

```markdown
Use approach B.
```

write:

```markdown
## Approach A

Tried on 2026-09-03.

Result:

Failed because the input dimensions were incompatible with the
existing preprocessing pipeline.

Do not retry unless the preprocessing representation changes.

## Approach B

Current implementation.

Result:

Successfully validated on ...
```

This is especially important for:

* HPC debugging
* scientific experiments
* model architectures
* data preprocessing
* APIs
* deployment
* dependency conflicts

---

# 13. Always Preserve Sources and Provenance

Agent-generated information should not silently become project fact.

Where appropriate, record:

```markdown
## Source

NASA documentation:
...

Paper:
...

Repository:
...

Experiment:
...

Person/team:
...
```

Also distinguish:

```text
Observed fact
Decision
Recommendation
Assumption
Open question
```

For scientific work, this distinction is particularly important.

---

# 14. What Must Never Be Committed

Never put the following into the repository:

* API keys
* passwords
* access tokens
* SSH private keys
* authentication cookies
* personally identifiable information unless explicitly approved
* export-controlled information
* proprietary information
* restricted datasets
* secrets copied from `.env` files
* credentials produced during agent sessions

Use placeholders:

```text
OPENAI_API_KEY=<your-key>
```

instead of real values.

The repository itself explicitly states that credentials, tokens, proprietary data, and restricted information must never be committed.

---

# 15. End Every Significant Agent Session With a Handoff

Before closing ChatGPT, Claude, Codex, or another agent, ask it:

```text
Prepare a handoff for the next agent session.

Update the project context with:

1. objective of this session
2. work completed
3. files changed
4. commands/tests run
5. results
6. decisions made
7. failed approaches
8. unresolved issues
9. exact next recommended step

Do not include conversational history.
Do not include secrets.
Write only durable information useful to another agent.
```

Then review the generated summary before committing it.

The human remains responsible for ensuring the information is correct.

---

# 16. Starting a New Agent Session

When starting a new session, the user should point the agent at the repository context rather than re-explaining everything manually.

For example:

```text
You are continuing work on this project.

First read:

- AGENTS.md
- projects/<project>/README.md
- projects/<project>/project.yaml
- projects/<project>/status/current.md
- projects/<project>/status/decisions.md
- relevant project knowledge

Then inspect:

git status
git log --oneline -10
git diff

Summarize your understanding of:

1. project objective
2. current state
3. unresolved problem
4. next action

Then continue the work.
```

For coding agents with repository access, this can become part of `AGENTS.md` so it happens automatically.

---

# 17. Recommended Daily Workflow

The workflow should look like this:

```text
Start agent session
       │
       ▼
Read AGENTS.md
       │
       ▼
Read project context
       │
       ▼
Inspect Git state
       │
       ▼
Perform work
       │
       ▼
Run tests / evaluations
       │
       ▼
Update project knowledge
       │
       ▼
Update current status
       │
       ▼
Record important decisions
       │
       ▼
Commit + Pull Request
       │
       ▼
Next agent can continue
```

The important principle is:

```text
Chat is working memory.

Git is durable memory.
```

---

# 18. Example Contribution

Suppose an engineer spends two hours with ChatGPT debugging a NASA NCCS SLURM training problem.

The conversation discovers:

* jobs work on one GPU
* jobs work on two GPUs
* eight GPUs hang
* NCCL initialization is likely involved
* three environment-variable changes were tested
* none worked
* the next experiment is known

Do **not** create:

```text
chatgpt-conversation-2026-09-04.txt
```

Instead update:

```text
projects/<project>/status/current.md
```

with the current problem and next step.

If the debugging process reveals a generally useful NCCS procedure, extract that into:

```text
integrations/
```

or:

```text
skills/.../diagnose-slurm-gpu-jobs/
```

That produces reusable institutional knowledge rather than storing conversation logs.

---

# 19. Pull Request Workflow

Contributors should normally work through Git:

```bash
git checkout main
git pull

git checkout -b docs/add-<project>-agent-context
```

Make the changes:

```bash
git add .
git commit -m "Add <project> agent context"
git push -u origin docs/add-<project>-agent-context
```

Then open a pull request.

The PR should explain:

```markdown
## What

Added persistent agent context for <project>.

## Why

Allows new ChatGPT/Codex/Claude sessions to reconstruct the
project state without relying on previous chat history.

## Added

- project context
- agent instructions
- current status
- technical decisions

## Validation

Reviewed with the project team and checked for credentials or
restricted information.
```

Before submitting, verify:

* no secrets are present
* commands and links were checked
* owners/sources are identified where appropriate
* project-specific content has not unnecessarily been placed in shared areas
* scripts or procedures were tested when applicable

---

# 20. The Rule of Thumb

When deciding where something from an AI session belongs, ask:

### Is it only relevant to this project?

Put it under:

```text
projects/<project>/
```

### Is it a fact or reference used by multiple projects?

Put it under:

```text
knowledge/
```

### Is it something an agent should know how to do repeatedly?

Put it under:

```text
skills/
```

### Is it a reusable agent persona or role?

Put it under:

```text
agents/
```

### Is it about interacting with an external system?

Put it under:

```text
integrations/
```

### Is it testing whether an agent behaves correctly?

Put it under:

```text
evals/
```

And when uncertain:

> Start project-specific and promote later.

That matches the intended lifecycle of `ilab-agentic-ai`:

```text
Project knowledge
       ↓
Shared knowledge
       ↓
Repeatable skill
       ↓
Evaluated capability
```
