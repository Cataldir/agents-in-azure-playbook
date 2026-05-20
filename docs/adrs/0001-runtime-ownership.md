# ADR 0001: Runtime Ownership Is Explicit

## Status

Accepted.

## Context

Agent systems can be built entirely through managed product surfaces, entirely through application code, or through a hybrid. The risk is not the choice itself. The risk is hiding the choice until an incident forces everyone to discover who owns routing, memory, identity, tool approval, and retries.

Microsoft Foundry can provide model access, evaluation, tracing, governance, prompt agents, workflow agents, and hosted-agent runtime capabilities. A product team still owns the application contract that users depend on.

## Decision

The sample makes runtime ownership explicit:

- Prompt-agent creation and invocation sits behind the Code Agents sample label.
- Hosted Agents use Foundry as the managed runtime, while the adapter code still owns request translation and app behavior.
- Custom Agents own the runtime directly through ports and adapters.

Foundry can be the model, evaluation, tracing, governance, and hosted-runtime surface. Product runtime ownership remains an explicit design decision.

## Consequences

Teams can change hosting choices without pretending that product behavior moved with a checkbox. Tests can exercise routing, memory, and protocol boundaries locally, before Azure resources or credentials exist.
