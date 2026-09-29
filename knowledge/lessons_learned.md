# Lessons Learned

Practical lessons from building and running agentic AI workflows on ILAB/ADAPT.

## Index

**Platforms and cost**
- [NMC AI Hub credits are limited](#nmc-ai-hub-credits-are-limited)
- [Match the model to the task](#match-the-model-to-the-task)
- [ChatGSFC Agent Builder works, but with friction](#chatgsfc-agent-builder-works-but-with-friction)
- [VS Code with Claude or Codex extensions is easier to work with](#vs-code-with-claude-or-codex-extensions-is-easier-to-work-with)

**VS Code on ADAPT and Discover**
- [Run compute-heavy work in a JupyterHub session](#run-compute-heavy-work-in-a-jupyterhub-session)
- [Connecting VS Code to Discover may be difficult](#connecting-vs-code-to-discover-may-be-difficult)
- [Close notebooks before letting the agent edit them](#close-notebooks-before-letting-the-agent-edit-them)
- [Check the environment before any pip install](#check-the-environment-before-any-pip-install)

**Working practices**
- [Use a repo as a persistent agent workspace](#use-a-repo-as-a-persistent-agent-workspace)
- [End each session with a daily recap](#end-each-session-with-a-daily-recap)
- [Start with a skills file for persistent preferences](#start-with-a-skills-file-for-persistent-preferences)
- [Require permission before the agent writes or edits](#require-permission-before-the-agent-writes-or-edits)
- [Give each project an AGENTS.md](#give-each-project-an-agentsmd)
- [Have the agent write up bugs and dead ends](#have-the-agent-write-up-bugs-and-dead-ends)
- [Keep notebook versions in git instead of copies](#keep-notebook-versions-in-git-instead-of-copies)

**Checking the agent's work**
- [Running without errors is not the same as correct](#running-without-errors-is-not-the-same-as-correct)
- [Ask the agent how results were computed](#ask-the-agent-how-results-were-computed)
- [Ask for loud failures, not silent fallbacks](#ask-for-loud-failures-not-silent-fallbacks)
- [Use a second agent to check the work](#use-a-second-agent-to-check-the-work)
- [Be specific about missing data](#be-specific-about-missing-data)
- [Visualize outputs to catch errors](#visualize-outputs-to-catch-errors)


---

## Platforms and cost

### NMC AI Hub credits are limited

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `nmc-ai-hub`, `cost`, `tokens`

**Lesson:** The NMC AI Hub doesn't come with many credits. Scientific workflows use a lot of tokens, so we will probably need to pay for more.

**Recommendation:**
- Plan for token costs when scoping scientific workflow projects.

---

### Match the model to the task

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `models`, `cost`, `tokens`

**Lesson:** Not every task needs the most capable (and most expensive) model. Matching the model to the work saves credits and is often faster.

**Recommendation:**

| Kind of work | Claude | Codex (OpenAI) |
|---|---|---|
| Hardest problems: new methods, tricky debugging, long multi-step agent runs | Fable 5.1 | GPT-6 Astra |
| Complex work: design, debugging, reviewing results, big refactors | Opus 5.5 | GPT-6 Astra or GPT-6.1 Sol |
| Everyday coding: writing functions, notebook edits, routine analysis | Sonnet 5.5 | GPT-6.1 Sol |
| Simple tasks: formatting, summaries, renaming, writing up notes | Haiku 4.5 | GPT-6 Luna |

- Most tools let you switch models mid-session (in Claude Code, type `/model`), so change when the kind of work changes.
- Both tools also have an **effort** (reasoning) setting. Lowering effort on a strong model is another way to save tokens on easy tasks.
- Model names change every few months. Check the current lists before relying on this table:
  - Claude: https://docs.claude.com/en/docs/about-claude/models/overview
  - Codex: https://developers.openai.com/codex/models
- Models available through the NMC AI Hub or ChatGSFC may differ from these lists.

---


---

### ChatGSFC Agent Builder works, but with friction

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `chatgsfc`, `agent-builder`, `file-search`

**Context:** You can build an agent in ChatGSFC with the Agent Builder and add files for it to search.

**Limitations:**
- The context window may not keep up with a long conversation.
- You have to move a lot of information by hand (download, upload, cut and paste) between ChatGSFC, ADAPT/JupyterHub, and your files.

**Lesson:** It's fine for lightweight use, but moving everything by hand slows down real development work.

---

### VS Code with Claude or Codex extensions is easier to work with

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `vs-code`, `claude-code`, `codex`

**Lesson:** VS Code with the Claude or Codex extension is much easier to work with than a chat-only interface. The assistant can:
- Read and write files directly
- Connect to the internet, which helps a lot when working with repos

**Recommendation:**
- Use VS Code with an AI extension for development work on ADAPT instead of copying things in and out of a chat window.

---

## VS Code on ADAPT and Discover

### Run compute-heavy work in a JupyterHub session

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `adapt`, `vs-code`, `jupyterhub`, `compute`

**Lesson:** When VS Code is connected to ADAPT over SSH, anything you or the agent runs there uses ADAPT's shared resources. Running heavy processing that way can overwhelm ADAPT for everyone.

**Recommendation:**
- Use the VS Code session for editing, light scripting, and file work.
- Run compute-heavy processes in an appropriate JupyterHub session.

---

### Connecting VS Code to Discover may be difficult

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `discover`, `vs-code`, `ssh`

**Lesson:** We had trouble connecting VS Code to Discover. We haven't checked whether that's still the case.

**Recommendation:**
- If you get it working, please update this entry with the steps.

---

### Close notebooks before letting the agent edit them

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `jupyter`, `notebooks`, `adapt`

**What happened:** If a notebook is open in JupyterHub on ADAPT while the agent edits the file, Jupyter's saves (including autosave) can overwrite the agent's changes.

**Recommendation:**
1. Close the notebook in JupyterHub.
2. Let the agent edit it.
3. Reopen the notebook to see the changes.

---

### Check the environment before any pip install

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `adapt`, `jupyter-kernels`, `pip`, `environments`

**What happened:** In PACE-VCF, a `pip install` run to fix one kernel went into `~/.local` as a `--user` install. That broke a different kernel that had worked for months. Also, a kernel named like an isolated environment turned out to point at a shared interpreter.

**Lesson:** On ADAPT, a `pip install` without the right environment activated can change every kernel that shares that Python version, not just the one you're working on. Agents will readily suggest or run `pip install` to fix an import error.

**Recommendation:**
- Before installing anything, check which interpreter is really in use (in a notebook cell: `import sys; print(sys.executable)`). Don't trust the kernel's display name.
- Install into an isolated conda env or venv, never with `--user`.
- Don't let the agent install packages without asking first.

**References:** [user-site pip install write-up](../projects/PACE-VCF/knowledge/troubleshooting/user-site-pip-install-environment-contamination.md)

---

## Working practices

### Use a repo as a persistent agent workspace

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `workflow`, `git`, `skills`, `best-practice`

**Lesson:** A repo gives the agent something like persistent memory. Everything it needs lives in one place and carries over between sessions.

**Recommendation:** Keep these in the repo:
- All the reference documents the agent needs
- Skills files (reusable instructions for common tasks)
- A daily README or status file recording what was done and what's next

---

### End each session with a daily recap

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `workflow`, `status-file`, `best-practice`

**Lesson:** The agent doesn't remember earlier sessions unless you give it something to read.

**Recommendation:**
- At the end of every session, have the agent write a recap to a status file in the repo.
- At the start of the next session, ask the agent to read that file first.

---

### Start with a skills file for persistent preferences

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `skills`, `preferences`, `best-practice`

**Lesson:** Putting your preferences in a skills file once saves you from repeating them every session.

**Recommendation:** Start with a skills file that covers things like:
- How detailed you want code comments to be
- What to put in file headers
- Checking in with you before writing or editing files

---

### Require permission before the agent writes or edits

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `permissions`, `safety`, `best-practice`

**Lesson:** Don't let the agent write or edit files without asking you first.

**Recommendation:**
- Set your AI extension so file writes and edits need your approval.
- Put this rule in your skills file as well (see [Start with a skills file for persistent preferences](#start-with-a-skills-file-for-persistent-preferences)).

---

### Give each project an AGENTS.md

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `agents-md`, `guardrails`, `best-practice`

**Lesson:** A short `AGENTS.md` in the project folder tells any agent the ground rules before it starts working.

**Recommendation:** Include things like:
- Project status (active, shelved) and what is or isn't runnable
- Don't invent results, experiments, or validation that isn't documented
- Project-specific pitfalls (for example, which of two R² definitions a number uses)
- Never add credentials, restricted data, or non-public code

**References:** [PACE-VCF AGENTS.md](../projects/PACE-VCF/AGENTS.md)

---

### Have the agent write up bugs and dead ends

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `documentation`, `troubleshooting`, `best-practice`

**Lesson:** Once a bug is fixed, the agent is well placed to write it up while the details are fresh. Dead ends are worth recording too. Without a record, a future person or agent will try the same thing again.

**Recommendation:**
- After each real bug, have the agent write a short note with **Symptom**, **Confirmed cause**, **Resolution**, and **General lesson**.
- Record approaches that didn't work and why (for example, the Earth Engine pixel limit in PACE-VCF).
- Review the write-up before committing.

**References:** [PACE-VCF troubleshooting folder](../projects/PACE-VCF/knowledge/troubleshooting/)

---

### Keep notebook versions in git instead of copies

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `notebooks`, `git`, `workflow`

**What happened:** In PACE-VCF, notebooks were versioned by copying (`3k`, `3l`, ...). One copy was made from an older version and quietly undid a bug fix. Nobody noticed until much later.

**Recommendation:**
- Keep one working notebook per step and use git for its history.
- If you do keep copies, record which one is canonical in the README or status file so the agent edits the right one.

**References:** [thermal-diff regression write-up](../projects/PACE-VCF/knowledge/troubleshooting/scale-thermal-diff-regression.md)

---

## Checking the agent's work

### Running without errors is not the same as correct

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `validation`, `silent-bugs`, `best-practice`

**What happened:** In PACE-VCF, several bugs gave wrong results without raising any error:
- A stray `]` split a list, and 40 metrics silently dropped out.
- Two thermal bands were 0% valid in every tile because of a scaling check.
- 0.1% missing data in an input spread to 99% of a filter's output.

**Lesson:** Code that runs cleanly can still be wrong, whether you or the agent wrote it.

**Recommendation:** Ask the agent to add quick sanity checks and look at the results:
- Counts (how many items or features actually came through?)
- Percent valid or NaN at each step
- Array shapes and value ranges

**References:** [PACE-VCF troubleshooting folder](../projects/PACE-VCF/knowledge/troubleshooting/)

---

### Ask the agent how results were computed

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `validation`, `metrics`, `best-practice`

**What happened:** In PACE-VCF, test-set leakage in feature selection turned up only after asking "is this R² train or test, and is there a real holdout?" Nothing in the output showed it. A headline RMSE was also off by about 1.5 points because per-tile values were averaged without weighting by pixel count.

**Recommendation:** Before trusting or reporting a number, ask the agent:
- Is this train, validation, or test? Was the test set used for any choices?
- Which definition of the metric is this?
- Is this averaged across groups? Should it be weighted?

**References:** [test-set leakage write-up](../projects/PACE-VCF/knowledge/troubleshooting/test-set-leakage-in-monte-carlo-selection.md), [unweighted RMSE write-up](../projects/PACE-VCF/knowledge/troubleshooting/unweighted-vs-pixel-weighted-rmse.md)

---

### Ask for loud failures, not silent fallbacks

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `code-review`, `silent-bugs`, `best-practice`

**What happened:** In PACE-VCF, the inference code looked for the feature list that belonged to a model. When it couldn't find it, the code quietly used whichever feature list was newest. Predictions looked fine but were wrong.

**Lesson:** A "best guess" fallback turns an obvious error (file not found) into a hidden one (wrong file used).

**Recommendation:**
- Ask the agent to raise an error when a required file or value is missing, instead of guessing.
- When reviewing agent code, look for `try/except` blocks or fallbacks that hide problems.

**References:** [inference feature-mismatch write-up](../projects/PACE-VCF/knowledge/troubleshooting/inference-model-feature-mismatch.md)

---

### Use a second agent to check the work

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `validation`, `sub-agents`, `code-review`, `best-practice`

**Lesson:** An agent reviewing its own work tends to share the same assumptions and miss the same mistakes. A separate reviewer catches more.

**Recommendation:**
- Have a sub-agent, a fresh session, or a different model (or vendor) review the work. The reviewer shouldn't see the first agent's reasoning, only the code and results.
- Give the reviewer specific things to check, not just "review this." For example: data splits and leakage, metric definitions, missing-data handling, units and scaling, silent fallbacks.
- You still make the final call. A second agent is another check, not a replacement for your review.

---

### Be specific about missing data

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `missing-data`, `nodata`, `nan`, `best-practice`

**Lesson:** If you don't say how to handle missing data, the agent will pick something, and often won't tell you what. In PACE-VCF, 0.1% NaN in an input spread to 99% of a filter's output without any error.

**Recommendation:** Tell the agent, in the prompt or your skills file:
- What marks missing data (NaN, a fill value such as `-9999`, a QA mask)
- What to do with it: skip, mask, fill (and how), or stop with an error
- To report the percent missing at each step, so you can see if it grows unexpectedly
- To use NaN-aware functions when filtering or averaging (plain filters spread NaNs)

**References:** [box-filter NaN write-up](../projects/PACE-VCF/knowledge/troubleshooting/box-filter-nan-poisoning.md), [PACE-VCF scaling and NaN conventions](../projects/PACE-VCF/knowledge/algorithms/scaling-conventions-and-nan-handling.md)

---

### Visualize outputs to catch errors

**Date:** 2026-09-29
**Author:** Melanie Frost
**Tags:** `validation`, `visualization`, `best-practice`

**Lesson:** A quick plot shows problems that summary numbers hide. In PACE-VCF, the NaN-spreading bug above was first spotted because a map of the output was almost entirely blank.

**Recommendation:**
- Ask the agent to plot outputs at key steps: maps, histograms, before/after comparisons, predicted vs. actual.
- Have it save figures to files. You can check them later, and some agents can open image files and look at them too.
- If a plot doesn't appear in a notebook, don't assume there's nothing to show. Check the matplotlib backend (see the write-up below).

**References:** [box-filter NaN write-up](../projects/PACE-VCF/knowledge/troubleshooting/box-filter-nan-poisoning.md), [matplotlib silent-plot write-up](../projects/PACE-VCF/knowledge/troubleshooting/matplotlib-agg-backend-silent-plot-failure.md)

---

