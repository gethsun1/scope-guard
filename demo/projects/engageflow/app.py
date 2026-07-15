import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT = "engageflow"
STATE = Path("/state/engageflow.json")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        state = json.loads(STATE.read_text())
        if self.path == "/health":
            status = 200 if state["healthy"] else 503
            body = {"status": "healthy" if status == 200 else "unhealthy", "project": PROJECT,
                    "release": state["release"], "migration": state["migration"]}
        else:
            status, body = 404, {"detail": "not found"}
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(json.dumps({"service": PROJECT, "message": format % args}), flush=True)


HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8201"))), Handler).serve_forever()

