from __future__ import annotations

import pytest

from agents_in_azure_playbook.fakes import (
    EchoPeerAgent,
    EchoTool,
    FakeModel,
    FakeTelemetry,
    InMemoryMemory,
)
from agents_in_azure_playbook.ports import AgentRequest
from agents_in_azure_playbook.runtime import AgentRuntime, UnknownRouteError


def test_runtime_routes_default_requests_to_model_with_memory() -> None:
    memory = InMemoryMemory()
    telemetry = FakeTelemetry()
    model = FakeModel()
    runtime = AgentRuntime(model=model, memory=memory, telemetry=telemetry)

    remember_response = runtime.handle(
        AgentRequest(user_id="user-1", session_id="session-1", text="remember blue")
    )
    model_response = runtime.handle(
        AgentRequest(user_id="user-1", session_id="session-1", text="hello")
    )

    assert remember_response.route == "memory.write"
    assert model_response.route == "model"
    assert model_response.metadata["memory_count"] == "1"
    assert [event.name for event in telemetry.events].count(
        "runtime.request.completed"
    ) == 2


def test_runtime_keeps_mcp_tools_and_a2a_peers_on_separate_planes() -> None:
    tool = EchoTool()
    peer = EchoPeerAgent()
    runtime = AgentRuntime(
        model=FakeModel(),
        memory=InMemoryMemory(),
        telemetry=FakeTelemetry(),
        tools={"planner": tool},
        peers={"planner": peer},
    )

    tool_response = runtime.handle(
        AgentRequest(
            user_id="user-1",
            session_id="session-1",
            text="mcp planner find inventory",
        )
    )
    peer_response = runtime.handle(
        AgentRequest(
            user_id="user-1",
            session_id="session-1",
            text="a2a planner make plan",
        )
    )

    assert tool_response.route == "mcp.planner"
    assert tool.invocations[0].payload == "find inventory"
    assert peer_response.route == "a2a.planner"
    assert peer.messages[0].message == "make plan"


def test_runtime_rejects_unknown_boundary_targets() -> None:
    runtime = AgentRuntime(
        model=FakeModel(), memory=InMemoryMemory(), telemetry=FakeTelemetry()
    )

    with pytest.raises(UnknownRouteError):
        runtime.handle(
            AgentRequest(
                user_id="user-1",
                session_id="session-1",
                text="mcp missing payload",
            )
        )


def test_runtime_reads_memory_from_requested_tier_only() -> None:
    runtime = AgentRuntime(
        model=FakeModel(), memory=InMemoryMemory(), telemetry=FakeTelemetry()
    )
    runtime.handle(
        AgentRequest(
            user_id="user-1",
            session_id="session-1",
            text="remember durable fact",
            memory_tier="durable",
        )
    )

    session_response = runtime.handle(
        AgentRequest(
            user_id="user-1",
            session_id="session-1",
            text="recall",
            memory_tier="session",
        )
    )
    durable_response = runtime.handle(
        AgentRequest(
            user_id="user-1",
            session_id="session-1",
            text="recall",
            memory_tier="durable",
        )
    )

    assert session_response.text == "No memory found."
    assert durable_response.text == "durable fact"
