# ADR 0003: MCP And A2A Protocol Split

## Status

Accepted.

## Context

MCP and A2A solve different problems. Treating them as interchangeable agent plumbing makes the system harder to secure and harder to reason about.

MCP is a tool and capability plane. It exposes actions and context to a model or agent runtime. A2A is a peer-agent application plane. It exposes another agent as an application participant with its own identity, behavior, and contract.

Foundry incoming A2A is currently preview, requires the Responses protocol, supports A2A protocol version 0.3, uses Microsoft Entra authentication, and is text-only in the documented preview.

## Decision

The custom runtime keeps separate ports and routes:

- `mcp <tool> <payload>` invokes a ToolPort.
- `a2a <peer> <message>` invokes a PeerAgentPort.

The names can overlap, but the plane determines which boundary is used. A tool called `planner` and a peer agent called `planner` are not the same dependency.

## Consequences

Approval policy, logging, authentication, and failure handling can differ by plane. Tests can prove that MCP calls do not accidentally route to peer agents and A2A calls do not accidentally route to tools.
