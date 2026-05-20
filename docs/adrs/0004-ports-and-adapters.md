# ADR 0004: Ports And Adapters For Runtime Code

## Status

Accepted.

## Context

Agent samples often wire directly from HTTP handlers to model SDK calls. That is convenient, but it makes local tests depend on credentials and hides the application boundary behind the SDK boundary.

This repository needs a compact runtime that runs without Azure credentials and still maps cleanly to Foundry, hosted agents, MCP, A2A, memory, and telemetry concepts.

## Decision

Use ports and adapters:

- Protocols define model, memory, tool, peer-agent, and telemetry boundaries.
- Dataclasses define request, response, memory, tool, peer, and event contracts.
- The runtime depends only on ports.
- FastAPI, Foundry SDK, and local HTTP samples are adapters, not the core runtime.

## Consequences

Tests can use fake ports. Azure SDK usage stays optional. The same runtime concepts can be explained in code-first, hosted, and custom-runtime posts without rewriting the mental model each time.
