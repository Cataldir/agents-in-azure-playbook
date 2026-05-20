"""Dependency-light HTTP app for the Custom Agents architecture label."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents_in_azure_playbook.fakes import (
    EchoPeerAgent,
    EchoTool,
    FakeModel,
    FakeTelemetry,
    InMemoryMemory,
)
from agents_in_azure_playbook.ports import AgentRequest
from agents_in_azure_playbook.runtime import AgentRuntime

runtime = AgentRuntime(
    model=FakeModel(prefix="custom-agent"),
    memory=InMemoryMemory(),
    telemetry=FakeTelemetry(),
    tools={"catalog": EchoTool()},
    peers={"planner": EchoPeerAgent()},
)


class RuntimeHandler(BaseHTTPRequestHandler):
    """HTTP adapter around the custom runtime."""

    def do_GET(self) -> None:
        """Serve a small health endpoint."""

        if self.path != "/health":
            self.send_error(404)
            return
        self._send_json({"status": "ok"})

    def do_POST(self) -> None:
        """Serve the local invoke endpoint."""

        if self.path != "/invoke":
            self.send_error(404)
            return

        content_length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        text = payload.get("text", "") if isinstance(payload, dict) else ""
        response = runtime.handle(
            AgentRequest(user_id="local-user", session_id="local-session", text=str(text))
        )
        self._send_json({"text": response.text, "route": response.route})

    def _send_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    """Run the local custom-agent sample server."""

    server = ThreadingHTTPServer(("127.0.0.1", 8081), RuntimeHandler)
    print("Listening on http://127.0.0.1:8081")
    server.serve_forever()


if __name__ == "__main__":
    main()
