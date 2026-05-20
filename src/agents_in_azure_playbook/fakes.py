"""In-memory adapters for local tests and samples."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from agents_in_azure_playbook.ports import (
    AgentRequest,
    AgentResponse,
    MemoryPort,
    MemoryRecord,
    MemoryTier,
    ModelPort,
    PeerAgentPort,
    PeerAgentRequest,
    TelemetryEvent,
    TelemetryPort,
    ToolPort,
    ToolRequest,
    ToolResult,
)


@dataclass(slots=True)
class FakeModel(ModelPort):
    """Deterministic model adapter for local runtime tests."""

    prefix: str = "model"
    calls: list[AgentRequest] = field(default_factory=list)

    def complete(
        self, request: AgentRequest, memories: Sequence[MemoryRecord]
    ) -> AgentResponse:
        self.calls.append(request)
        return AgentResponse(
            text=f"{self.prefix}: {request.text}",
            route="model",
            metadata={"memory_count": str(len(memories))},
        )


@dataclass(slots=True)
class InMemoryMemory(MemoryPort):
    """Memory adapter that stores records by user and memory tier."""

    records: dict[tuple[str, MemoryTier], list[MemoryRecord]] = field(
        default_factory=dict
    )

    def load(self, user_id: str, tier: MemoryTier) -> Sequence[MemoryRecord]:
        return tuple(self.records.get((user_id, tier), ()))

    def store(self, record: MemoryRecord) -> None:
        self.records.setdefault((record.user_id, record.tier), []).append(record)


@dataclass(slots=True)
class FakeTelemetry(TelemetryPort):
    """Telemetry adapter that records events in memory."""

    events: list[TelemetryEvent] = field(default_factory=list)

    def record(self, event: TelemetryEvent) -> None:
        self.events.append(event)


@dataclass(slots=True)
class EchoTool(ToolPort):
    """MCP-style tool adapter that echoes payloads."""

    invocations: list[ToolRequest] = field(default_factory=list)

    def invoke_tool(self, request: ToolRequest) -> ToolResult:
        self.invocations.append(request)
        return ToolResult(
            content=f"tool:{request.name}:{request.payload}",
            metadata={"tool": request.name},
        )


@dataclass(slots=True)
class EchoPeerAgent(PeerAgentPort):
    """A2A-style peer adapter that echoes messages."""

    messages: list[PeerAgentRequest] = field(default_factory=list)

    def send_message(self, request: PeerAgentRequest) -> AgentResponse:
        self.messages.append(request)
        return AgentResponse(
            text=f"peer:{request.name}:{request.message}",
            route=f"a2a.{request.name}",
            metadata={"peer": request.name},
        )
