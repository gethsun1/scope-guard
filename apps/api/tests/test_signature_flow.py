import hashlib
import json
from typing import Any

from fastapi.testclient import TestClient
from scope_guard import engine
from scope_guard.main import app


class FakeRunner(engine.Runner):
    def __init__(self) -> None:
        self.rd = {"healthy": True, "release": 1, "migration": 0}
        self.engage = {"healthy": True, "release": 1, "migration": 0}
        self.snapshot: dict[str, Any] | None = None

    def digest(self, value: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    async def execute(self, operation: str) -> dict[str, Any]:
        if operation == "snapshot":
            self.snapshot = dict(self.rd)
        if operation == "deploy_rdsocial":
            self.rd["release"] += 1
        if operation == "migrate_rdsocial":
            self.rd["migration"] += 1
        if operation == "fail_rdsocial":
            self.rd["healthy"] = False
        if operation == "rollback_rdsocial" and self.snapshot:
            self.rd = dict(self.snapshot)
        if operation == "reset":
            self.rd = {"healthy": True, "release": 1, "migration": 0}
            self.engage = {"healthy": True, "release": 1, "migration": 0}
        return {"ok": True, "rdsocial_hash": self.digest(self.rd),
                "engageflow_hash": self.digest(self.engage), "engageflow": self.engage}


client = TestClient(app)
headers = {"X-Demo-Token": "scope-guard-demo"}


def run_flow(failure: bool = False) -> dict[str, Any]:
    engine.TASKS.clear()
    engine.runner = FakeRunner()
    created = client.post("/api/tasks", headers=headers,
        json={"instruction": "Update and deploy RD Social without modifying EngageFlow",
              "failure_injection": failure})
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert client.post(f"/api/tasks/{task_id}/plan", headers=headers).status_code == 200
    assert client.post(f"/api/tasks/{task_id}/approve-boundary", headers=headers).status_code == 200
    execution = client.post(f"/api/tasks/{task_id}/execute", headers=headers)
    assert execution.status_code == 200
    body = execution.json()
    assert body["status"] == "awaiting_approval"
    decisions = [row["decision"]["decision"] for row in body["actions"]]
    assert decisions == ["ALLOW", "BLOCK_PROTECTED_RESOURCE", "ALLOW_WITH_APPROVAL"]
    assert body["actions"][1]["decision"]["suggested_correction"] == "systemctl restart rdsocial-api"
    final = client.post(f"/api/tasks/{task_id}/actions/restart-rdsocial/approve", headers=headers)
    assert final.status_code == 200
    return final.json()


def test_complete_signature_flow() -> None:
    final = run_flow()
    assert final["status"] == "completed"
    assert final["report"]["audit_integrity"] is True
    assert len(final["report"]["blocked_actions"]) == 1


def test_failure_rolls_back_target_only() -> None:
    final = run_flow(True)
    assert final["status"] == "rolled_back"
    assert final["report"]["rollback"] == {"triggered": True, "success": True}
    assert engine.runner.engage == {"healthy": True, "release": 1, "migration": 0}  # type: ignore[attr-defined]


def test_demo_auth_and_reset() -> None:
    assert client.post("/api/tasks", json={"instruction": "a sufficiently long task"}).status_code == 401
    engine.runner = FakeRunner()
    assert client.post("/api/demo/reset", headers=headers).json()["protected_integrity"] is True
