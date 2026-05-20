"""Self-hosted runtime router for the custom-agent architecture path.

The runtime uses Strategy-like ports for model, memory, tool, peer-agent, and
telemetry behavior. It deliberately keeps MCP-style tools separate from A2A-style
peer agents so the protocol boundary stays visible in tests and samples.
"""

from __future__ import annotations

from collections.abc import Mapping

from agents_in_azure_playbook.ports import (
    AgentRequest,
    AgentResponse,
    MemoryPort,
    MemoryRecord,
    ModelPort,
    PeerAgentPort,
    PeerAgentRequest,
    TelemetryEvent,
    TelemetryPort,
    ToolPort,
    ToolRequest,
)


class UnknownRouteError(ValueError):
    """Raised when a runtime request names an unregistered tool or peer."""


class AgentRuntime:
    """Routes agent requests across model, memory, MCP, and A2A boundaries."""

    def __init__(
        self,
        model: ModelPort,
        memory: MemoryPort,
        telemetry: TelemetryPort,
        tools: Mapping[str, ToolPort] | None = None,
        peers: Mapping[str, PeerAgentPort] | None = None,
    ) -> None:
        self._model = model
        self._memory = memory
        self._telemetry = telemetry
        self._tools = dict(tools or {})
        self._peers = dict(peers or {})

    def handle(self, request: AgentRequest) -> AgentResponse:
        """Handle a request and return the selected route response."""

        normalized_text = request.text.strip()
        if not normalized_text:
            return AgentResponse(text="Empty input.", route="error.empty_input")

        self._record_event("runtime.request.received", "ingress", request)

        try:
            if normalized_text.startswith("remember "):
                response = self._remember(
                    request, normalized_text.removeprefix("remember ")
                )
            elif normalized_text == "recall" or normalized_text.startswith("recall "):
                response = self._recall(request)
            else:
                command = _parse_boundary_command(normalized_text)
                if command is None:
                    response = self._call_model(request)
                elif command.plane == "mcp":
                    response = self._call_tool(request, command.target, command.payload)
                else:
                    response = self._call_peer(request, command.target, command.payload)
        except Exception:
            self._record_event("runtime.request.failed", "error", request)
            raise

        self._record_event("runtime.request.completed", response.route, request)
        return response

    def _remember(self, request: AgentRequest, content: str) -> AgentResponse:
        memory_content = content.strip()
        if not memory_content:
            return AgentResponse(
                text="Nothing to remember.", route="memory.write.empty"
            )

        record = MemoryRecord(
            user_id=request.user_id,
            session_id=request.session_id,
            tier=request.memory_tier,
            content=memory_content,
            source="user",
        )
        self._memory.store(record)
        return AgentResponse(
            text="Memory stored.",
            route="memory.write",
            metadata={"memory_tier": request.memory_tier},
        )

    def _recall(self, request: AgentRequest) -> AgentResponse:
        memories = self._memory.load(request.user_id, request.memory_tier)
        if not memories:
            return AgentResponse(
                text="No memory found.",
                route="memory.read",
                metadata={"memory_count": "0"},
            )

        memory_text = "\n".join(memory.content for memory in memories)
        return AgentResponse(
            text=memory_text,
            route="memory.read",
            metadata={"memory_count": str(len(memories))},
        )

    def _call_model(self, request: AgentRequest) -> AgentResponse:
        memories = self._memory.load(request.user_id, request.memory_tier)
        return self._model.complete(request, memories)

    def _call_tool(
        self, request: AgentRequest, tool_name: str, payload: str
    ) -> AgentResponse:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise UnknownRouteError(f"No MCP tool registered for '{tool_name}'.")

        tool_request = ToolRequest(
            name=tool_name,
            payload=payload,
            caller_user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata,
        )
        tool_result = tool.invoke_tool(tool_request)
        return AgentResponse(
            text=tool_result.content,
            route=f"mcp.{tool_name}",
            metadata=tool_result.metadata,
        )

    def _call_peer(
        self, request: AgentRequest, peer_name: str, payload: str
    ) -> AgentResponse:
        peer = self._peers.get(peer_name)
        if peer is None:
            raise UnknownRouteError(f"No A2A peer registered for '{peer_name}'.")

        peer_request = PeerAgentRequest(
            name=peer_name,
            message=payload,
            caller_user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata,
        )
        return peer.send_message(peer_request)

    def _record_event(
        self, event_name: str, route: str, request: AgentRequest
    ) -> None:
        self._telemetry.record(
            TelemetryEvent(
                name=event_name,
                route=route,
                attributes={
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "text_length": str(len(request.text)),
                },
            )
        )


class _BoundaryCommand:
    """Parsed runtime command for a protocol boundary route."""

    def __init__(self, plane: str, target: str, payload: str) -> None:
        self.plane = plane
        self.target = target
        self.payload = payload


def _parse_boundary_command(text: str) -> _BoundaryCommand | None:
    plane, separator, remainder = text.partition(" ")
    if separator == "" or plane not in {"mcp", "a2a"}:
        return None

    target, target_separator, payload = remainder.strip().partition(" ")
    if target_separator == "" or not target:
        raise UnknownRouteError(
            f"Boundary command '{plane}' requires a target and payload."
        )

    return _BoundaryCommand(plane=plane, target=target, payload=payload.strip())
