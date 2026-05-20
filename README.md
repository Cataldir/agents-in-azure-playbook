# Agents in Azure Playbook

Compact, public-safe Python samples for explaining agent architecture choices in Microsoft Foundry and Azure. The repository is designed to support blog posts about three practical implementation paths:

- Code Agents: a code-first sample label for creating and invoking a prompt agent through the Foundry SDK boundary.
- Hosted Agents: a hosted-agent manifest and FastAPI Responses adapter pattern, with validation and operations notes.
- Custom Agents: a self-hosted runtime that keeps model, MCP-style tool, A2A-style peer-agent, memory, and telemetry boundaries explicit.

Microsoft Foundry Agent Service officially names the current agent types as prompt agents, workflow agents, and hosted agents. In this repository, Code Agents and Custom Agents are explanatory labels for architecture paths. They are not official product categories.

## Why This Exists

Agent projects tend to mix product capability, application runtime, protocol routing, identity, and memory into one blurry layer. That makes demos fast, but production ownership vague. This sample keeps the runtime boundary visible:

- Foundry can be the model, evaluation, tracing, hosted-runtime, and governance surface.
- Product teams still own application behavior, data contracts, memory policy, tool approval, and failure handling.
- MCP is treated as a tool and capability plane.
- A2A is treated as a peer-agent application plane.

The code is fresh and intentionally small. Holiday Peak Hub is credited as architectural inspiration for public-safe sample framing and Azure-oriented operating notes. Holiday Peak Hub is MIT-compatible source material, but this repository does not copy its private values, logs, or implementation.

## Repository Map

```text
src/agents_in_azure_playbook/
  ports.py              # Protocols and dataclasses for model, memory, tools, peers, telemetry
  runtime.py            # Self-hosted runtime router for model, memory, MCP-style, and A2A-style paths
  responses_adapter.py  # Adapter between OpenAI Responses-shaped payloads and the runtime
  manifest.py           # Hosted-agent manifest validation and public-safety checks
  fakes.py              # In-memory ports for local tests and samples
samples/
  code-agent-foundry/   # Optional Foundry SDK prompt-agent boundary sample
  hosted-agent-fastapi/ # FastAPI adapter sample plus agent.yaml and Dockerfile
  custom-agent-runtime/ # Dependency-light HTTP runtime sample
docs/adrs/              # Architecture decisions
docs/playbooks/         # Hosted-agent operations notes
tests/                  # Local tests with no Azure credentials required
```

## Run Locally

From this repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pytest -q
python -m ruff check src tests
python -m mypy src tests
```

Python 3.11 or later is supported. The local tests use only fake ports and do not require Azure credentials.

## Optional Samples

The Foundry SDK sample is guarded by import and configuration checks. It exits with a clear message if Azure packages or required environment variables are missing.

```powershell
python -m pip install -e .[foundry]
$env:AZURE_AI_PROJECT_ENDPOINT = "https://<account>.services.ai.azure.com/api/projects/<project>"
$env:AZURE_AI_MODEL_DEPLOYMENT = "<model-deployment-name>"
python samples/code-agent-foundry/create_prompt_agent.py
```

The hosted FastAPI sample is similarly optional:

```powershell
python -m pip install -e .[fastapi]
python samples/hosted-agent-fastapi/app.py
```

## Hosted-Agent Facts Encoded Here

- Hosted agents are currently a preview capability in Microsoft Foundry Agent Service.
- Hosted-agent containers should use linux/amd64 images.
- Image tags should be unique and immutable for deployments; do not use latest.
- The Azure Container Registry endpoint currently needs public reachability for hosted-agent image pulls.
- The Foundry project managed identity needs pull permission on the registry for platform image operations.
- The runtime agent identity is different from the project managed identity. Runtime permissions for tools and downstream services belong on the agent identity.
- Incoming Foundry A2A is preview, requires the Responses protocol, supports A2A protocol version 0.3, uses Microsoft Entra authentication, and is text-only in the current documented preview.

## Public-Safety Rules

This repo is intended to be safe for public publishing. Do not add:

- Secrets, tokens, passwords, keys, or connection strings.
- Cloud account identifiers, directory identifiers, object identifiers, or private endpoints.
- Private logs, incident output, customer names, or internal project names.
- Image tags that imply mutable production state, such as latest.

Use placeholders such as `<registry-name>`, `<project-name>`, and `<agent-name>` in docs and samples.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
