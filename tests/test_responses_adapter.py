from __future__ import annotations

import pytest

from agents_in_azure_playbook.fakes import FakeModel, FakeTelemetry, InMemoryMemory
from agents_in_azure_playbook.ports import AgentResponse
from agents_in_azure_playbook.responses_adapter import (
    adapt_responses_request,
    extract_input_text,
    handle_responses_payload,
    to_responses_payload,
)
from agents_in_azure_playbook.runtime import AgentRuntime


def test_extract_input_text_from_string_input() -> None:
    assert extract_input_text({"input": " hello "}) == "hello"


def test_extract_input_text_from_responses_message_list() -> None:
    payload: dict[str, object] = {
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "first"},
                    {"type": "input_text", "text": "second"},
                ],
            }
        ]
    }

    assert extract_input_text(payload) == "first\nsecond"


def test_adapt_responses_request_preserves_conversation_and_metadata() -> None:
    request = adapt_responses_request(
        {
            "conversation": "conversation-1",
            "input": "hello",
            "metadata": {"source": "test", "ignored": 3},
        }
    )

    assert request.text == "hello"
    assert request.conversation_id == "conversation-1"
    assert request.metadata == {"source": "test"}


def test_to_responses_payload_includes_output_text_and_route_metadata() -> None:
    payload = to_responses_payload(
        AgentResponse(text="done", route="model", metadata={"memory_count": "0"}),
        response_id="resp_test",
    )

    assert payload["output_text"] == "done"
    assert payload["metadata"] == {"memory_count": "0", "route": "model"}


def test_handle_responses_payload_uses_runtime_adapter_boundary() -> None:
    runtime = AgentRuntime(
        model=FakeModel(prefix="adapter"),
        memory=InMemoryMemory(),
        telemetry=FakeTelemetry(),
    )

    payload = handle_responses_payload(
        {"conversation": "conversation-1", "input": "hello"}, runtime
    )

    assert payload["output_text"] == "adapter: hello"
    assert payload["metadata"] == {"memory_count": "0", "route": "model"}


def test_extract_input_text_rejects_empty_payloads() -> None:
    with pytest.raises(ValueError):
        extract_input_text({"input": "   "})
