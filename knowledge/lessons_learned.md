# Lessons Learned

Practical lessons from building and running agentic AI workflows on ILAB/ADAPT.

## Index

**Platforms and cost**
- [NMC AI Hub credits are limited](#nmc-ai-hub-credits-are-limited)
- [ChatGSFC Agent Builder works, but with friction](#chatgsfc-agent-builder-works-but-with-friction)
- [VS Code with Claude or Codex extensions is easier to work with](#vs-code-with-claude-or-codex-extensions-is-easier-to-work-with)

**VS Code on ADAPT and Discover**
- [Run compute-heavy work in a JupyterHub session](#run-compute-heavy-work-in-a-jupyterhub-session)
- [Connecting VS Code to Discover may be difficult](#connecting-vs-code-to-discover-may-be-difficult)
- [Close notebooks before letting the agent edit them](#close-notebooks-before-letting-the-agent-edit-them)

**Working practices**
- [Use a repo as a persistent agent workspace](#use-a-repo-as-a-persistent-agent-workspace)
- [End each session with a daily recap](#end-each-session-with-a-daily-recap)
- [Start with a skills file for persistent preferences](#start-with-a-skills-file-for-persistent-preferences)
- [Require permission before the agent writes or edits](#require-permission-before-the-agent-writes-or-edits)

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
