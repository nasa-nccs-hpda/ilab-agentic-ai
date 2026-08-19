# NASA Mantle Local LLM Access

This guide explains how to access the **NASA Mantle LLM inference server** and use the available models from:

* LiteLLM Playground
* `curl`
* Python
* Visual Studio Code Chat
* Visual Studio Code Agent mode

The inference service is provided through **LiteLLM**, which exposes an OpenAI-compatible API.

---

## 1. NASA Mantle Endpoint

### LiteLLM Web Interface

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/
```

### API Base URL

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1
```

### Chat Completions Endpoint

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions
```

Mantle uses the OpenAI-compatible **Chat Completions API**.

Despite the name, Chat Completions supports full multi-turn conversations and, for compatible models, tool calling for agentic workflows.

---

# 2. Log In to LiteLLM

Open:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/
```

Authenticate using the configured NASA authentication method.

After logging in, the LiteLLM AI Gateway provides several useful sections:

* **Virtual Keys** — create and manage API keys
* **Playground** — interact with deployed models
* **Models + Endpoints** — view available models
* **Usage** — view API usage

---

# 3. Create an API Key

From the LiteLLM sidebar, select:

```text
Virtual Keys
```

Click:

```text
+ Create New Key
```

Give the key a descriptive alias, such as:

```text
yourname-vscode
```

or:

```text
yourname-development
```

Select the models that the key should be allowed to access and create the key.

LiteLLM will generate a Virtual Key similar to:

```text
sk-...
```

Copy and securely store the key.

> **Important:** Treat your API key like a password. Do not commit it to Git, place it directly in source code or notebooks, or share it with another user.

If a key is accidentally exposed, revoke it under **Virtual Keys** and create a new one.

---

# 4. Test a Model in the Playground

Before configuring an external application, you can verify access directly through LiteLLM.

From the sidebar, select:

```text
Playground
```

Select a model and enter a prompt such as:

```text
Write a Python function that calculates the mean of a list.
```

If the model responds, your account and model access are working.

---

# 5. Configure Your Terminal

For command-line and Python access, it is convenient to define two environment variables.

## macOS / Linux

```bash
export LITELLM_API_KEY="sk-your-key-here"
export LITELLM_BASE_URL="https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1"
```

Verify them with:

```bash
echo $LITELLM_BASE_URL
```

Avoid printing your API key in shared terminals, logs, screenshots, or recordings.

### Persistent Configuration

If you use `zsh`, you can add the variables to:

```text
~/.zshrc
```

For example:

```bash
export LITELLM_API_KEY="sk-your-key-here"
export LITELLM_BASE_URL="https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1"
```

Then reload your configuration:

```bash
source ~/.zshrc
```

For environments where storing secrets in shell configuration files is not appropriate, use your organization's approved credential-management mechanism instead.

---

# 6. Check Available Models

Models available to your Virtual Key can be retrieved from:

```text
GET /v1/models
```

Run:

```bash
curl "$LITELLM_BASE_URL/models" \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

A response may look similar to:

```json
{
  "data": [
    {
      "id": "auto",
      "object": "model"
    },
    {
      "id": "mistral-large-3-675b",
      "object": "model"
    },
    {
      "id": "mistral-large-3-675b-nvfp4",
      "object": "model"
    },
    {
      "id": "devstral-2-123b",
      "object": "model"
    },
    {
      "id": "mistral-medium-3-5-128b",
      "object": "model"
    }
  ],
  "object": "list"
}
```

The exact list may change as models are added or removed from Mantle.

Use the exact `id` returned by `/v1/models` when making API requests.

---

# 7. Test Chat from the Command Line

Mantle exposes an OpenAI-compatible Chat Completions endpoint.

For example:

```bash
curl "$LITELLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "Explain what a transformer is in one paragraph."
      }
    ]
  }'
```

A successful response contains an assistant message under:

```text
choices[0].message.content
```

---

# 8. Conversations

The Chat Completions API supports multi-turn conversations.

Conversation history is represented using the `messages` array.

For example:

```json
{
  "model": "auto",
  "messages": [
    {
      "role": "system",
      "content": "You are a scientific programming assistant."
    },
    {
      "role": "user",
      "content": "What is PyTorch?"
    },
    {
      "role": "assistant",
      "content": "PyTorch is a machine learning framework..."
    },
    {
      "role": "user",
      "content": "Show me a simple neural network using it."
    }
  ]
}
```

Applications such as VS Code manage this conversation history automatically.

---

# 9. Connect NASA Mantle to VS Code

VS Code supports custom OpenAI-compatible language model endpoints.

This allows Mantle models to be used directly from **VS Code Chat** and, when tool calling is supported, **Agent mode**.

## Step 1 — Open VS Code Chat

Open VS Code.

Use the Command Palette:

### macOS

```text
Cmd + Shift + P
```

### Windows / Linux

```text
Ctrl + Shift + P
```

Search for:

```text
Chat: Manage Language Models
```

---

## Step 2 — Add a Custom Endpoint

Select:

```text
Add Models
```

Then select:

```text
Custom Endpoint
```

Use a recognizable provider name such as:

```text
NASA Mantle
```

Enter the LiteLLM Virtual Key created earlier when VS Code requests the API key.

For the API type, select:

```text
Chat Completions
```

> Mantle uses Chat Completions for both conversational and agent-capable workflows. You do not need to select the Responses API to have a conversation or use agents.

VS Code will create or open its custom language model configuration.

---

# 10. Configure NASA Mantle in VS Code

Configure the endpoint as follows:

```json
[
  {
    "name": "NASA Mantle",
    "vendor": "customendpoint",
    "apiKey": "${input:chat.lm.secret.-51f8e3f5}",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "auto",
        "name": "NASA - Auto",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      }
    ]
  }
]
```

### Important

The value:

```text
${input:chat.lm.secret.-51f8e3f5}
```

is an example of a VS Code-generated secret reference.

**Do not assume your secret identifier will be identical.**

When you add the endpoint through **Chat: Manage Language Models**, VS Code should create the appropriate secret reference for your installation.

Keep the value generated by VS Code.

Do not replace it with somebody else's secret ID, and do not put the actual `sk-...` API key directly into a configuration file that could be shared or committed.

---

# 11. Understanding the Configuration

The important fields are:

### Provider

```json
"vendor": "customendpoint"
```

This tells VS Code that the model is provided through a custom endpoint.

### API Type

```json
"apiType": "chat-completions"
```

Mantle uses the OpenAI-compatible Chat Completions protocol.

This supports normal conversations as well as tool calls.

### Model

```json
"id": "auto"
```

The model ID must correspond to a model returned by:

```bash
curl "$LITELLM_BASE_URL/models" \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

### Endpoint

```json
"url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions"
```

The URL must point to the **Chat Completions endpoint**, not just the Mantle website or `/v1` base URL.

### Tool Calling

```json
"toolCalling": true
```

This tells VS Code that the model can participate in tool-calling workflows.

Tool calling is required for many VS Code Agent capabilities.

---

# 12. Reload VS Code

After modifying the configuration, open the Command Palette:

```text
Cmd + Shift + P
```

or:

```text
Ctrl + Shift + P
```

and run:

```text
Developer: Reload Window
```

---

# 13. Select the NASA Model in VS Code Chat

Open the VS Code **Chat** panel.

At the bottom of the Chat input, click the current model name to open the model picker.

Select:

```text
NASA - Auto
```

You can now have normal conversations with the model.

For example:

```text
Explain what this Python function does.
```

```text
What is the difference between a list and a tuple?
```

```text
Explain the architecture of this repository.
```

```text
How could I improve this class?
```

The conversation is sent through:

```text
VS Code
    ↓
NASA Mantle
    ↓
LiteLLM
    ↓
Model
```

---

# 14. Using Agent Mode

VS Code Agent mode extends normal conversation by allowing the model to request tools.

For example, an agent can potentially:

* inspect files
* search the workspace
* modify source code
* create files
* inspect errors
* invoke supported VS Code tools
* run terminal commands, subject to VS Code permissions and confirmation settings

The architecture is approximately:

```text
              VS Code Agent
                    |
                    v
              NASA Mantle
                    |
                    v
                 LiteLLM
                    |
                    v
                  Model
                    |
              tool request
                    |
                    v
              VS Code Tools
             /      |       \
            /       |        \
         Files    Search    Terminal
            \       |        /
             \      |       /
                    v
             tool results
                    |
                    v
                  Model
```

The model decides which tool should be called, while **VS Code executes the actual tool**.

---

# 15. Enable BYOK Models for Agent Host

Depending on your VS Code version and which agent interface you are using, custom/BYOK models may need to be explicitly enabled for Agent Host sessions.

Open:

```text
Cmd + Shift + P
```

and select:

```text
Preferences: Open User Settings (JSON)
```

Add:

```json
"chat.agentHost.byokModels.enabled": true
```

For example:

```json
{
  "chat.agentHost.byokModels.enabled": true
}
```

If your settings file already contains other settings, add the property to the existing JSON object rather than replacing the file.

After changing this setting, fully reload or restart VS Code.

---

# 16. Chat vs. Agent

The same Mantle model can be used for both.

You do **not** need separate APIs for conversation and agents.

## Chat

A normal conversation looks like:

```text
User
  ↓
Model
  ↓
Response
```

Example:

```text
Explain this repository to me.
```

## Agent

An agentic interaction looks like:

```text
User
  ↓
Model
  ↓
Tool Call
  ↓
VS Code
  ↓
Tool Result
  ↓
Model
  ↓
Response / Additional Tool Call
```

Example:

```text
Look through this repository, identify why the tests are failing,
fix the problem, and run the tests again.
```

The important capability for agents is **tool calling**.

It is not necessary to switch from Chat Completions to the Responses API simply to use agents.

---

# 17. Using a Specific Model

The default configuration uses:

```json
"id": "auto"
```

which allows the Mantle/LiteLLM configuration to determine the appropriate backend model.

You can also explicitly configure a model.

For example:

```json
{
  "id": "devstral-2-123b",
  "name": "NASA - Devstral 2 123B",
  "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
  "toolCalling": true
}
```

This can be useful when you want predictable model behavior rather than automatic routing.

---

# 18. Configure Multiple NASA Models

Multiple models can be exposed in the VS Code model picker.

For example:

```json
[
  {
    "name": "NASA Mantle",
    "vendor": "customendpoint",
    "apiKey": "${input:chat.lm.secret.-51f8e3f5}",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "auto",
        "name": "NASA - Auto",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      },
      {
        "id": "devstral-2-123b",
        "name": "NASA - Devstral 2 123B",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      },
      {
        "id": "mistral-large-3-675b",
        "name": "NASA - Mistral Large 3 675B",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      },
      {
        "id": "mistral-large-3-675b-nvfp4",
        "name": "NASA - Mistral Large 3 675B NVFP4",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      },
      {
        "id": "mistral-medium-3-5-128b",
        "name": "NASA - Mistral Medium 3.5 128B",
        "url": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions",
        "toolCalling": true
      }
    ]
  }
]
```

Only advertise:

```json
"toolCalling": true
```

for models that actually support tool calling through Mantle.

---

# 19. Test Tool Calling

Before relying on a model for Agent mode, you can verify that tool calling works through LiteLLM.

For example:

```bash
curl "$LITELLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "What is the weather in Baltimore?"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get the current weather for a city",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string"
              }
            },
            "required": ["city"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'
```

For this test, the `get_weather` function does not actually need to exist.

The goal is to determine whether the model generates a tool request.

A successful response should contain a `tool_calls` field similar to:

```json
{
  "tool_calls": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\":\"Baltimore\"}"
      }
    }
  ]
}
```

If the model returns a valid `tool_calls` response, the Mantle → LiteLLM → model path is supporting tool calling.

---

# 20. Python

Because Mantle exposes an OpenAI-compatible API, it can be used with the OpenAI Python client.

Install:

```bash
pip install openai
```

Then:

```python
import os

from openai import OpenAI


client = OpenAI(
    api_key=os.environ["LITELLM_API_KEY"],
    base_url="https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1",
)

response = client.chat.completions.create(
    model="auto",
    messages=[
        {
            "role": "user",
            "content": "Explain satellite remote sensing in one paragraph.",
        }
    ],
)

print(response.choices[0].message.content)
```

---

# 21. Use Standard OpenAI Environment Variables

Some OpenAI-compatible applications automatically look for:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
```

You can configure Mantle using:

```bash
export OPEN
```
