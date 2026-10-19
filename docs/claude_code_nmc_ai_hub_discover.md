# Claude Code CLI Setup on NASA Discover

Setup instructions for running Claude Code on NASA Discover using the NASA LiteLLM proxy (NMC AI Hub).

This guide parallels [`codex_nmc_ai_hub_discover.md`](https://github.com/nasa-nccs-hpda/ilab-agentic-ai/blob/main/docs/codex_nmc_ai_hub_discover.md).

> **NASA configuration:** The Mission AI Hub configuration supplied by users maps Claude Code’s `sonnet`, `opus`, and `haiku` selections to NASA LiteLLM aliases. These values are provided as the site configuration; the guide has not been tested live on Discover.

## 1. Install Claude Code

Use Anthropic's native Linux installer. Discover users who encounter restricted temporary directories can set `TMPDIR=/tmp`, as in the Codex guide:

```bash
TMPDIR=/tmp bash -c 'curl -fsSL https://claude.ai/install.sh | bash'
```

Ensure the user-local bin directory is on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Persist it in `~/.bashrc` if necessary. Verify:

```bash
claude --version
```

To update later:

```bash
claude update
```

The native installer is preferred over the deprecated npm installation method. Do not use `sudo`.

## 2. Configure NASA LiteLLM API Key

Reuse the same `NASA_LITELLM_API_KEY` used in the Codex guide. Add the secret to your shell environment using an institutionally approved storage method. If your existing Codex setup already exports it, do not duplicate it.

```bash
export NASA_LITELLM_API_KEY="YOUR_API_KEY"
```

For persistence, place the export in `~/.bashrc` only if permitted by local credential-handling policy, and restrict access to the file. Reload your environment:

```bash
source ~/.bashrc
```

Verify without printing the secret:

```bash
test -n "$NASA_LITELLM_API_KEY" && echo "API key configured"
```

## 3. Configure Claude Code for NASA Mission AI Hub

Create your user-level settings file:

```bash
mkdir -p ~/.claude
chmod 700 ~/.claude
vi ~/.claude/settings.json
```

Use the NASA Mission AI Hub model aliases and proxy settings:

```json
{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4.5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5-thinking",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-5-opus-thinking",
    "DISABLE_TELEMETRY": "1",
    "ANTHROPIC_BASE_URL": "https://proxy.fast.luna.nasa.gov/",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    "CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING": "1"
  },
  "model": "sonnet",
  "theme": "auto"
}
```

The site-provided configuration also includes `"ANTHROPIC_AUTH_TOKEN": "sk-YOUR-API-KEY"` inside `env`. To avoid storing the secret in a JSON file, **export the same token in your shell instead**:

```bash
export ANTHROPIC_AUTH_TOKEN="$NASA_LITELLM_API_KEY"
unset ANTHROPIC_API_KEY
```

To persist the mapping, add the `export ANTHROPIC_AUTH_TOKEN=...` line to `~/.bashrc` **after** the line that defines `NASA_LITELLM_API_KEY`. If your site requires the token inside `settings.json`, insert it under `env` in your private `~/.claude/settings.json`, use the actual secret rather than the placeholder, and restrict permissions:

```bash
chmod 600 ~/.claude/settings.json
```

Never commit your token to a repository. The URL is the proxy root; do not append `/v1/messages`.

### Model selection

`"model": "sonnet"` selects the configured `claude-sonnet-5-thinking` alias by default. The model aliases are supplied by NASA Mission AI Hub, not inferred from public Anthropic naming conventions. In Claude Code, use `/model` to switch models interactively, or start with `claude --model opus` or `claude --model haiku` when supported by your installed version.

### Validate configuration

```bash
python -m json.tool ~/.claude/settings.json >/dev/null && echo "Valid JSON"
test -n "$ANTHROPIC_AUTH_TOKEN" && echo "Token configured"
claude --version
```

Then launch `claude` and try a simple read-only repository question. This validates actual authentication and model/tool compatibility more reliably than listing gateway models.

## 4. Run Claude Code

Navigate to your project:

```bash
cd /path/to/project
```

### Standard / Safe

Read and write operations require approval according to the default permission rules:

```bash
claude --permission-mode default
```

### Auto-Accept Edits

Claude Code can modify files without asking about each edit, while potentially risky shell operations can still request approval:

```bash
claude --permission-mode acceptEdits
```

This is a practical default when using the AI Hub gateway and working interactively.

### Autonomous With Safety Review (if supported)

On versions and model configurations that support auto mode, Claude Code can use background checks instead of prompting for routine operations:

```bash
claude --permission-mode auto
```

**Important:** Auto mode is availability- and model-dependent, so it may not work with a NASA LiteLLM model alias. Unlike Codex's `-a never -s workspace-write`, `auto` is not itself a filesystem sandbox. Claude Code sandbox settings require separate configuration.

### Read-Only Planning

```bash
claude --permission-mode plan
```

Useful for architecture review, debugging plans, and exploring the repository before approving edits.

### Full Access / Unsafe

```bash
claude --dangerously-skip-permissions
```

This bypasses normal approval checks and is **not sandboxed**. Do not use it on shared Discover login nodes, production storage, or untrusted repositories. Only use it inside a properly isolated, approved development environment where damage is contained. Site policy or managed settings may prohibit this mode.

## 5. Resume a Session

Resume the latest session in the project:

```bash
claude --continue
```

Choose from previous sessions:

```bash
claude --resume
```

Resume while accepting edits:

```bash
claude --permission-mode acceptEdits --continue
```

## 6. Troubleshooting

**`claude: command not found`:** Restart the shell, source `~/.bashrc`, and verify `~/.local/bin` is in `PATH`.

**Authentication errors or an unexpected Anthropic login prompt:** Check that `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and the selected `model` / `ANTHROPIC_DEFAULT_*_MODEL` aliases are set in the shell that launches Claude Code, and that a conflicting `ANTHROPIC_API_KEY` is unset. Check local authentication policy before changing sign-in settings.

**`model not found` or unsupported request:** The proxy may not expose the selected alias through the Anthropic Messages API. Verify the exact Mission AI Hub alias and your token’s access to it.

**Requests work for chat but fail during coding:** Claude Code requires tool-use support, streaming and other Anthropic Messages compatibility features. Ask the NASA AI Hub team to verify support for `/v1/messages` for your selected model alias.

**Automatic mode unavailable:** Fall back to `acceptEdits`; do not automatically substitute `--dangerously-skip-permissions`.

## Recommended Discover Workflow

For interactive development:

```bash
cd /path/to/project
claude --permission-mode acceptEdits
```

For safe review and planning:

```bash
cd /path/to/project
claude --permission-mode plan
```

For autonomous operation where the model and site policies support it:

```bash
cd /path/to/project
claude --permission-mode auto
```

**Recommended:** Use `acceptEdits` initially, test end-to-end tool execution against the NASA gateway, then configure sandboxing and/or auto mode if supported.

**Use carefully:** `--dangerously-skip-permissions` is an unrestricted permissions bypass, not an equivalent to Codex's workspace-write sandbox.

## References

- [Claude Code installation](https://code.claude.com/docs/en/setup)
- [Claude Code permissions](https://code.claude.com/docs/en/permission-modes)
- [LiteLLM: Connect Claude Code](https://docs.litellm.ai/docs/proxy/client_setup/claude_code)
- [Existing NASA Discover Codex guide](https://github.com/nasa-nccs-hpda/ilab-agentic-ai/blob/main/docs/codex_nmc_ai_hub_discover.md)
