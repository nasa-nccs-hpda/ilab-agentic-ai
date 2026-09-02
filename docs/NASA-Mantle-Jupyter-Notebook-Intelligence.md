# NASA Mantle LLM Access from Jupyter Notebook Intelligence

This guide documents how to configure **Notebook Intelligence** in NASA JupyterHub / JupyterLab to use the **NASA Mantle LLM service**.

Mantle exposes an OpenAI-compatible API, which allows Notebook Intelligence to use Mantle models for:

* Chat
* Notebook assistance
* Inline code completion
* Streaming responses

## 1. NASA Mantle Endpoint

Mantle API base URL:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1
```

The corresponding Chat Completions endpoint is:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions
```

Notebook Intelligence should be configured with the **base URL**, not the full `/chat/completions` endpoint.

## 2. Create a Mantle API Key

Open the NASA Mantle LiteLLM interface:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/
```

Authenticate using the configured NASA authentication method.

From the LiteLLM interface:

1. Open **Virtual Keys**.
2. Select **Create New Key**.
3. Give the key a descriptive name.
4. Select the models that the key should be allowed to access.
5. Create the key.
6. Copy the generated key.

The key will look similar to:

```text
sk-XXXXXXXX
```

> **Important**
>
> Treat the API key like a password. Do not commit the real key to Git, include it in documentation, or share it with other users.

## 3. Verify Mantle Access from JupyterHub

Before configuring Notebook Intelligence, verify that the JupyterHub environment can reach Mantle.

Set the API key temporarily:

```bash
export LITELLM_API_KEY="sk-YOUR-KEY"
```

Check the models available to your key:

```bash
curl -s \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

A successful response should contain model IDs similar to:

```json
{
  "data": [
    {
      "id": "auto"
    },
    {
      "id": "mistral-large-3-675b"
    },
    {
      "id": "mistral-large-3-675b-nvfp4"
    },
    {
      "id": "devstral-2-123b"
    },
    {
      "id": "mistral-medium-3-5-128b"
    }
  ]
}
```

The exact list may change as models are added or removed from Mantle.

## 4. Verify Streaming Chat Completions

Notebook Intelligence requires a model capable of streaming responses.

Test streaming directly from the JupyterHub terminal:

```bash
curl -N \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "Say hello from JupyterHub"
      }
    ],
    "stream": true
  }'
```

A successful response will contain multiple Server-Sent Events resembling:

```text
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: {"choices":[{"delta":{"content":" from"}}]}
data: {"choices":[{"delta":{"content":" JupyterHub"}}]}
data: [DONE]
```

If this works, the network connection, API key, model, and streaming interface are functioning correctly.

## 5. Configure Notebook Intelligence

Notebook Intelligence uses the following configuration file:

```text
~/.jupyter/nbi-config.json
```

Create or edit the file:

```bash
nano ~/.jupyter/nbi-config.json
```

Use the following configuration:

```json
{
    "chat_model": {
        "provider": "openai-compatible",
        "model": "openai-compatible-chat-model",
        "properties": [
            {
                "id": "api_key",
                "name": "API key",
                "description": "API key",
                "value": "sk-XXXX",
                "optional": false
            },
            {
                "id": "model_id",
                "name": "Model",
                "description": "Model (must support streaming)",
                "value": "auto",
                "optional": false
            },
            {
                "id": "base_url",
                "name": "Base URL",
                "description": "Base URL",
                "value": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1",
                "optional": true
            },
            {
                "id": "context_window",
                "name": "Context window",
                "description": "Context window length",
                "value": "",
                "optional": true
            }
        ]
    },
    "inline_completion_model": {
        "provider": "openai-compatible",
        "model": "openai-compatible-inline-completion-model",
        "properties": [
            {
                "id": "api_key",
                "name": "API key",
                "description": "API key",
                "value": "sk-XXXX",
                "optional": false
            },
            {
                "id": "model_id",
                "name": "Model",
                "description": "Model",
                "value": "auto",
                "optional": false
            },
            {
                "id": "base_url",
                "name": "Base URL",
                "description": "Base URL",
                "value": "https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1",
                "optional": true
            },
            {
                "id": "context_window",
                "name": "Context window",
                "description": "Context window length",
                "value": "",
                "optional": true
            }
        ]
    }
}
```

Replace:

```text
sk-XXXX
```

with your own Mantle Virtual Key.

## 6. Provider Selection

The important Notebook Intelligence setting is:

```json
"provider": "openai-compatible"
```

Mantle is implemented behind LiteLLM, but its externally exposed interface is an **OpenAI-compatible API**.

The corresponding Notebook Intelligence model implementations are:

```json
"model": "openai-compatible-chat-model"
```

for chat, and:

```json
"model": "openai-compatible-inline-completion-model"
```

for inline code completion.

## 7. Model Selection

The default configuration uses:

```json
"value": "auto"
```

for the model ID.

This allows Mantle to determine the appropriate backend model.

A specific model may also be selected. For example:

```json
"value": "devstral-2-123b"
```

Other currently available models may include:

```text
mistral-large-3-675b
mistral-large-3-675b-nvfp4
devstral-2-123b
mistral-medium-3-5-128b
```

Always verify the currently available models using:

```bash
curl -s \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

## 8. Restart JupyterLab

After changing:

```text
~/.jupyter/nbi-config.json
```

restart the JupyterHub / JupyterLab session.

A browser refresh alone may not reload the Notebook Intelligence backend configuration.

From JupyterHub, stop and restart the user server if necessary:

```text
Hub Control Panel
    ↓
Stop My Server
    ↓
Start My Server
```

Then reopen JupyterLab.

## 9. Test Notebook Intelligence

Open the Notebook Intelligence panel in JupyterLab and submit a simple prompt such as:

```text
Write a Python function that calculates the mean of a list.
```

You can also open a notebook and ask questions about existing code.

For inline completion, begin writing Python code inside a notebook cell and verify that Notebook Intelligence provides completion suggestions.

## 10. Architecture

The resulting architecture is:

```text
Jupyter Notebook
      |
      v
Notebook Intelligence
      |
      | OpenAI-compatible API
      v
NASA Mantle
      |
      v
LiteLLM Gateway
      |
      v
Configured LLM
```

For chat:

```text
Notebook Intelligence
        |
        v
POST /v1/chat/completions
        |
        v
NASA Mantle
        |
        v
Streaming response
```

## 11. Troubleshooting

### Mantle works with curl but Notebook Intelligence does not

If this command works:

```bash
curl https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

and streaming Chat Completions also work, then the Mantle service, network connection, and API key are functioning correctly.

Check the Notebook Intelligence configuration instead.

Confirm the configuration file exists:

```bash
ls -l ~/.jupyter/nbi-config.json
```

Validate that the JSON is syntactically correct:

```bash
python -m json.tool ~/.jupyter/nbi-config.json
```

The command should print the formatted JSON without an error.

### Wrong provider

Use:

```json
"provider": "openai-compatible"
```

rather than:

```json
"provider": "litellm-compatible"
```

for this configuration.

### Wrong URL

Use:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1
```

Do not use the web interface URL:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/
```

and do not place the full Chat Completions endpoint into the `base_url` field:

```text
https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions
```

Notebook Intelligence constructs the Chat Completions request using the configured base URL.

### API key issues

Verify the key directly:

```bash
curl -s \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

If this returns an authentication error, create or verify the Mantle Virtual Key.

### Model issues

Verify that the configured model exists:

```bash
curl -s \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/models \
  -H "Authorization: Bearer $LITELLM_API_KEY"
```

Then use the exact `id` returned by Mantle.

### Streaming issues

Notebook Intelligence chat expects streaming support.

Verify:

```bash
curl -N \
  https://mantle.scipai.sandbox.sciencecloud.nasa.gov/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "Streaming test"
      }
    ],
    "stream": true
  }'
```

The request should return incremental `data:` events followed by:

```text
data: [DONE]
```

## 12. Security

The configuration currently contains the Mantle API key:

```json
"value": "sk-XXXX"
```

Do not commit a populated `nbi-config.json` to Git.

If documenting the configuration in a repository, always use a placeholder:

```text
sk-XXXX
```

Recommended permissions for the local configuration file are:

```bash
chmod 600 ~/.jupyter/nbi-config.json
```

This restricts the file to the owning user.

If a Mantle API key is accidentally exposed, revoke it through the Mantle **Virtual Keys** interface and create a new key.
