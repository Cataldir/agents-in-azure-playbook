"""FastAPI Hosted Agent sample using the Responses adapter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Request
except ImportError:  # pragma: no cover - optional sample dependency
    print("Install optional packages first: python -m pip install -e .[fastapi]")
    raise

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents_in_azure_playbook.fakes import FakeModel, FakeTelemetry, InMemoryMemory
from agents_in_azure_playbook.responses_adapter import handle_responses_payload
from agents_in_azure_playbook.runtime import AgentRuntime

app = FastAPI(title="Agents in Azure Playbook Hosted Agent")

runtime = AgentRuntime(
    model=FakeModel(prefix="hosted-agent"),
    memory=InMemoryMemory(),
    telemetry=FakeTelemetry(),
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a basic health probe response."""

    return {"status": "ok"}


@app.post("/responses")
async def responses(request: Request) -> dict[str, object]:
    """Handle a compact Responses-compatible request."""

    payload: dict[str, Any] = await request.json()
    return handle_responses_payload(payload, runtime)


if __name__ == "__main__":  # pragma: no cover - local convenience entry point
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
