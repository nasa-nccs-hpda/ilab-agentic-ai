# Codex CLI Setup on NASA Discover

Setup instructions for running Codex CLI on NASA Discover using the NASA LiteLLM proxy.

## 1. Install Codex

```bash
TMPDIR=/tmp sh -c 'curl -fsSL https://chatgpt.com/codex/install.sh | sh'
```

Verify:

```bash
codex --version
```

To update Codex later, simply rerun the installation command.

## 2. Configure NASA LiteLLM API Key

Add your NASA LiteLLM API key to `~/.bashrc`:

```bash
export NASA_LITELLM_API_KEY="YOUR_API_KEY"
```

Reload your environment:

```bash
source ~/.bashrc
```

Verify that the key is available:

```bash
test -n "$NASA_LITELLM_API_KEY" && echo "API key configured"
```

## 3. Configure Codex

Create the Codex configuration directory:

```bash
mkdir -p ~/.codex
vi ~/.codex/config.toml
```

Add:

```toml
model_provider = "nasa"
model = "gpt-6-astra"

[model_providers.nasa]
name = "NASA LiteLLM"
base_url = "https://proxy.fast.luna.nasa.gov"
env_key = "NASA_LITELLM_API_KEY"
wire_api = "responses"

[projects."/gpfsm/dhome/jacaraba"]
trust_level = "trusted"

[projects."/gpfsm/dnb33/jacaraba"]
trust_level = "trusted"

[projects."/gpfsm/dnb33/jacaraba/development/imvi-atom"]
trust_level = "trusted"

[projects."/gpfsm/dnb06/projects/p295/jacaraba/imvi-atom"]
trust_level = "trusted"

[tui]
screen_reader_detection_done = true

[tui.model_availability_nux]
gpt-6-astra = 4
```

Update the trusted project paths for your Discover username and projects as needed.

## 4. Run Codex

Navigate to your project:

```bash
cd /path/to/project
```

### Standard / Safe

Codex can work in the repository but requests approval when additional permissions are needed:

```bash
codex -a on-request -s workspace-write
```

### Autonomous + Sandboxed

Codex works autonomously without approval prompts while remaining restricted to the workspace:

```bash
codex -a never -s workspace-write
```

This is the recommended mode for longer agentic coding tasks on Discover.

### Read-Only

Codex can inspect and analyze the repository without modifying it:

```bash
codex -s read-only
```

Useful for code review, debugging, and planning.

### Full Access / Unsafe

Codex runs autonomously without approval prompts or filesystem sandbox restrictions:

```bash
codex -a never -s danger-full-access
```

Use with caution. This allows Codex to execute commands and modify files outside the current repository.

## 5. Resume a Session

Resume the most recent Codex session:

```bash
codex resume --last
```

Resume autonomously:

```bash
codex -a never -s workspace-write resume --last
```

Resume with unrestricted access:

```bash
codex -a never -s danger-full-access resume --last
```

## Recommended Discover Workflow

For most autonomous development:

```bash
cd /path/to/project
codex -a never -s workspace-write
```

For trusted environments where Codex needs unrestricted access:

```bash
cd /path/to/project
codex -a never -s danger-full-access
```

**Recommended:** `never + workspace-write` = autonomous but sandboxed.

**Use carefully:** `never + danger-full-access` = autonomous and unrestricted.
