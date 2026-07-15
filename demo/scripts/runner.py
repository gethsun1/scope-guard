import hashlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

STATE = Path("/state")
ALLOWED = {"snapshot", "deploy_rdsocial", "migrate_rdsocial", "fail_rdsocial", "rollback_rdsocial", "status"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(operation: str) -> dict[str, object]:
    if operation not in ALLOWED:
        return {"ok": False, "decision": "BLOCK_UNKNOWN_RESOURCE", "operation": operation}
    rd, protected = STATE / "rdsocial.json", STATE / "engageflow.json"
    if operation == "snapshot":
        (STATE / "rdsocial.snapshot.json").write_bytes(rd.read_bytes())
    elif operation == "deploy_rdsocial":
        data = json.loads(rd.read_text()); data["release"] += 1; rd.write_text(json.dumps(data))
    elif operation == "migrate_rdsocial":
        data = json.loads(rd.read_text()); data["migration"] += 1; rd.write_text(json.dumps(data))
    elif operation == "fail_rdsocial":
        data = json.loads(rd.read_text()); data["healthy"] = False; rd.write_text(json.dumps(data))
    elif operation == "rollback_rdsocial":
        rd.write_bytes((STATE / "rdsocial.snapshot.json").read_bytes())
    return {"ok": True, "operation": operation, "rdsocial_hash": digest(rd),
            "engageflow_hash": digest(protected), "engageflow": json.loads(protected.read_text())}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.respond(200, {"status": "healthy", "runner": "predefined-actions-only"})
        else:
            self.respond(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length) or b"{}")
        if self.path != "/execute":
            self.respond(404, {"detail": "not found"}); return
        result = execute(str(request.get("operation", "")))
        self.respond(200 if result["ok"] else 403, result)

    def respond(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body).encode(); self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(json.dumps({"service": "demo-runner", "message": format % args}), flush=True)


HTTPServer(("0.0.0.0", 9000), Handler).serve_forever()

