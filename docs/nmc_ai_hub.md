# SETTING UP CODEX CLI WITH NASA AI HUB API KEY

## Instructions

### 1. Install Node.js and Codex CLI

**Windows**

* Download/install Node.js (`.msi`): https://nodejs.org/en/download
* In PowerShell:

```powershell
npm i -g @openai/codex
```

**Mac**

* Download/install Node.js (`.pkg`): https://nodejs.org/en/download
* In Terminal:

```bash
npm i -g @openai/codex
```

### 2. Get your NASA AI Hub Team Key

* Go to https://proxy.fast.luna.nasa.gov/ui
* Sign in with NASA Launchpad
* Create a Team Key and copy it using the copy button

  * Recommended: paste it into a secure document for recovery later

### 3. Set environment variables permanently

**Windows (PowerShell)**

```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your-team-key-here', 'User')
[System.Environment]::SetEnvironmentVariable('OPENAI_API_BASE', 'https://proxy.fast.luna.nasa.gov', 'User')
```

**Mac (Terminal, default zsh)**

```bash
echo 'export OPENAI_API_KEY="your-team-key-here"' >> ~/.zshrc
echo 'export OPENAI_API_BASE="https://proxy.fast.luna.nasa.gov"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Open the config file

**Windows**

```text
C:\Users\<your-username>\.codex\config.toml
```

or:

```text
%USERPROFILE%\.codex\config.toml
```

**Mac**

```text
/Users/<your-username>/.codex/config.toml
```

or:

```text
~/.codex/config.toml
```

### 5. Add the NASA AI Hub URL to the config

Add this as a new line:

```toml
openai_base_url = "https://proxy.fast.luna.nasa.gov"
```

### 6. Restart your terminal/VS Code and verify

```bash
codex doctor
```

It should show that authentication is provided by the environment.

### 7. Test Codex

```bash
codex "write a hello world in python"
```

## Useful Commands

**Start Codex**

From PowerShell (Windows) or Terminal (Mac):

```bash
codex
```

**Resume a previous session**

```bash
codex resume
```

**Resume the most recent session**

```bash
codex resume --last
```
