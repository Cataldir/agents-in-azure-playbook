# ADR 0002: Hosted Agents Preview Adoption

## Status

Accepted with constraints.

## Context

Hosted agents let teams deploy code-based agents as containers on Microsoft Foundry Agent Service. They are useful when prompt-only configuration is not enough and the team wants Foundry-managed hosting, scale, endpoint handling, identity integration, and observability.

The feature is currently documented as preview. Preview adoption should make operational assumptions visible instead of burying them in deployment scripts.

## Decision

The sample treats hosted agents as a preview deployment path and encodes the following constraints in docs and manifest validation:

- Use linux/amd64 container images.
- Use unique image tags; do not deploy latest.
- Keep the Azure Container Registry endpoint publicly reachable for platform image pulls while this limitation applies.
- Grant the Foundry project managed identity pull permission on the registry.
- Assign runtime access for downstream tools and services to the agent identity, not the project managed identity.
- Use the Responses protocol when the agent needs incoming Foundry A2A preview support.

## Consequences

The deployment contract is louder than the demo. A failed pull, wrong architecture image, mutable tag, or identity mix-up becomes a checklist item instead of a mystery.
