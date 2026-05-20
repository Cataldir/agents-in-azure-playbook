"""Ports and data contracts for the sample agent runtime.

The module follows ports-and-adapters with structural subtyping: the runtime
depends on protocols, and tests or production adapters supply implementations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

MemoryTier = Literal["ephemeral", "session", "durable"]


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Application-level request handled by the sample runtime."""

    user_id: str
    session_id: str
    text: str
    memory_tier: MemoryTier = "session"
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Application-level response returned by the sample runtime."""

    text: str
    route: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """A memory item scoped by user, session, and durability tier."""

    user_id: str
    session_id: str
    tier: MemoryTier
    content: str
    source: str


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """Request sent to an MCP-style tool or capability port."""

    name: str
    payload: str
    caller_user_id: str
    session_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Result returned by an MCP-style tool or capability port."""

    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PeerAgentRequest:
    """Request sent to an A2A-style peer-agent port."""

    name: str
    message: str
    caller_user_id: str
    session_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """Small telemetry envelope that avoids recording prompt text."""

    name: str
    route: str
    attributes: Mapping[str, str] = field(default_factory=dict)


class ModelPort(Protocol):
    """Model boundary used by prompt, hosted, or custom runtime adapters."""

    def complete(
        self, request: AgentRequest, memories: Sequence[MemoryRecord]
    ) -> AgentResponse:
        """Return a model response for the request and available memory."""


class MemoryPort(Protocol):
    """Memory boundary for ephemeral, session, and durable memory tiers."""

    def load(self, user_id: str, tier: MemoryTier) -> Sequence[MemoryRecord]:
        """Load memory records for a user and tier."""

    def store(self, record: MemoryRecord) -> None:
        """Store a memory record."""


class ToolPort(Protocol):
    """MCP-style capability boundary."""

    def invoke_tool(self, request: ToolRequest) -> ToolResult:
        """Invoke a named tool with a plain payload."""


class PeerAgentPort(Protocol):
    """A2A-style peer-agent boundary."""

    def send_message(self, request: PeerAgentRequest) -> AgentResponse:
        """Send a message to a peer agent and return its response."""


class TelemetryPort(Protocol):
    """Telemetry boundary for traces, metrics, and audit events."""

    def record(self, event: TelemetryEvent) -> None:
        """Record a telemetry event."""
