"""Adapter for OpenAI Responses-shaped payloads.

The Adapter pattern is used here because hosted-agent HTTP payloads and the
application runtime have different contracts. This module translates between
them without making the runtime depend on FastAPI or Azure SDK packages.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TypeGuard

from agents_in_azure_playbook.ports import AgentRequest, AgentResponse
from agents_in_azure_playbook.runtime import AgentRuntime


@dataclass(frozen=True, slots=True)
class ResponsesRequest:
    """Normalized request extracted from a Responses-style payload."""

    text: str
    conversation_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


def extract_input_text(payload: Mapping[str, object]) -> str:
    """Extract user text from common Responses API input shapes."""

    input_value = payload.get("input")
    if isinstance(input_value, str):
        return _require_text(input_value)

    if _is_sequence(input_value):
        text_fragments = list(_iter_text_fragments(input_value))
        return _require_text("\n".join(text_fragments))

    raise ValueError("Responses payload must include string or list input.")


def adapt_responses_request(payload: Mapping[str, object]) -> ResponsesRequest:
    """Normalize a Responses-style HTTP body into a runtime request shape."""

    conversation_value = payload.get("conversation") or payload.get(
        "conversation_id"
    )
    conversation_id = (
        conversation_value if isinstance(conversation_value, str) else None
    )
    metadata_value = payload.get("metadata")
    metadata = _string_mapping(metadata_value) if metadata_value is not None else {}
    return ResponsesRequest(
        text=extract_input_text(payload),
        conversation_id=conversation_id,
        metadata=metadata,
    )


def handle_responses_payload(
    payload: Mapping[str, object],
    runtime: AgentRuntime,
    *,
    default_user_id: str = "local-user",
    default_session_id: str = "local-session",
) -> dict[str, object]:
    """Handle a Responses-style payload through the runtime."""

    responses_request = adapt_responses_request(payload)
    runtime_request = AgentRequest(
        user_id=default_user_id,
        session_id=responses_request.conversation_id or default_session_id,
        text=responses_request.text,
        metadata=responses_request.metadata,
    )
    runtime_response = runtime.handle(runtime_request)
    return to_responses_payload(runtime_response)


def to_responses_payload(
    response: AgentResponse, response_id: str = "resp_local_sample"
) -> dict[str, object]:
    """Convert a runtime response to a compact Responses-compatible body."""

    metadata = dict(response.metadata)
    metadata["route"] = response.route
    return {
        "id": response_id,
        "object": "response",
        "status": "completed",
        "output": [
            {
                "id": f"msg_{response_id}",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": response.text,
                    }
                ],
            }
        ],
        "output_text": response.text,
        "metadata": metadata,
    }


def _iter_text_fragments(items: Iterable[object]) -> Iterable[str]:
    for item in items:
        if isinstance(item, str):
            yield item
            continue

        item_mapping = _mapping(item)
        if item_mapping is None:
            continue

        direct_text = item_mapping.get("text")
        if isinstance(direct_text, str):
            yield direct_text

        content_value = item_mapping.get("content")
        if isinstance(content_value, str):
            yield content_value
        elif _is_sequence(content_value):
            yield from _iter_content_fragments(content_value)


def _iter_content_fragments(items: Iterable[object]) -> Iterable[str]:
    for content_item in items:
        if isinstance(content_item, str):
            yield content_item
            continue

        content_mapping = _mapping(content_item)
        if content_mapping is None:
            continue

        text_value = content_mapping.get("text")
        if isinstance(text_value, str):
            yield text_value


def _require_text(value: str) -> str:
    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError("Responses input text cannot be empty.")
    return stripped_value


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        str(mapping_key): mapping_value
        for mapping_key, mapping_value in value.items()
        if isinstance(mapping_key, str)
    }


def _string_mapping(value: object) -> Mapping[str, str]:
    value_mapping = _mapping(value)
    if value_mapping is None:
        return {}
    return {
        mapping_key: mapping_value
        for mapping_key, mapping_value in value_mapping.items()
        if isinstance(mapping_value, str)
    }
