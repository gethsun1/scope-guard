from typing import Any

from fastapi.testclient import TestClient
from scope_guard import engine, planner
from scope_guard.main import app

client = TestClient(app)


def payload(actions: list[str], **changes: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "task": "Deploy RD Social without modifying EngageFlow",
        "proposed_actions": actions,
        "allowed_resources": ["rdsocial-asgi"],
        "protected_resources": ["engageflow-api"],
        "allowed_paths": ["/opt/rdsocial/**"],
        "protected_paths": ["/opt/engageflow/**"],
        "risk_tolerance": "strict",
    }
    value.update(changes)
    return value


def analyze(actions: list[str], **changes: Any) -> dict[str, Any]:
    response = client.post("/api/v1/asp/analyze", json=payload(actions, **changes))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    return response.json()  # type: ignore[no-any-return]


def test_protected_resource_is_blocked_without_demo_token() -> None:
    body = analyze(["systemctl restart engageflow-api"])
    assert body["verdict"] == "BLOCK"
    assert body["risk_score"] == 95
    assert "PROTECTED_RESOURCE_ACCESS" in body["decisions"][0]["policy_codes"]


def test_allowed_read_only_action_is_allowed() -> None:
    body = analyze(["cat /opt/rdsocial/config.py"])
    assert body["verdict"] == "ALLOW"
    assert body["risk_score"] == 10


def test_allowed_mutation_requires_approval() -> None:
    body = analyze(["systemctl restart rdsocial-asgi"])
    assert body["verdict"] == "REQUIRE_APPROVAL"
    assert body["risk_score"] == 60
    assert body["required_approvals"] == [{"action_index": 0, "reason": "Approved-scope mutation"}]


def test_protected_path_is_blocked() -> None:
    body = analyze(["cat /opt/engageflow/config.py"])
    assert body["verdict"] == "BLOCK"
    assert "PROTECTED_PATH_ACCESS" in body["decisions"][0]["policy_codes"]


def test_unknown_resource_is_denied_by_default() -> None:
    body = analyze(["systemctl restart redis"])
    assert body["verdict"] == "BLOCK"
    assert body["decisions"][0]["policy_codes"] == ["SG-UNKNOWN-001"]


def test_destructive_and_secret_actions_are_blocked() -> None:
    destructive = analyze(["rm -rf /opt/rdsocial"])
    secret = analyze(["cat /opt/rdsocial/.env"])
    assert destructive["decisions"][0]["policy_codes"] == ["SG-DESTRUCTIVE-001"]
    assert secret["decisions"][0]["policy_codes"] == ["SG-SECRET-001"]
    assert destructive["risk_score"] == secret["risk_score"] == 100


def test_mixed_plan_uses_most_restrictive_verdict() -> None:
    body = analyze(["cat /opt/rdsocial/config.py", "systemctl restart rdsocial-asgi",
                    "systemctl restart engageflow-api"])
    assert [item["verdict"] for item in body["decisions"]] == [
        "ALLOW", "REQUIRE_APPROVAL", "BLOCK"]
    assert body["verdict"] == "BLOCK"


def test_material_results_and_evidence_hash_are_deterministic() -> None:
    first = analyze(["cat /opt/rdsocial/config.py"])
    second = analyze(["cat /opt/rdsocial/config.py"])
    for field in ("evaluation_id", "verdict", "risk_score", "decisions", "evidence_hash"):
        assert first[field] == second[field]
    assert first["evaluated_at"] != second["evaluated_at"]


def test_invalid_action_bounds_and_unicode_are_rejected() -> None:
    assert client.post("/api/v1/asp/analyze", json=payload([])).status_code == 422
    assert client.post("/api/v1/asp/analyze", json=payload(["ls"] * 26)).status_code == 422
    assert client.post("/api/v1/asp/analyze", json=payload(["x" * 2001])).status_code == 422
    assert client.post("/api/v1/asp/analyze", json=payload(["cat\x00file"])).status_code == 422


def test_path_traversal_and_invalid_boundaries_are_denied() -> None:
    body = analyze(["cat /opt/rdsocial/../engageflow/config.py"])
    assert body["verdict"] == "BLOCK"
    assert body["decisions"][0]["policy_codes"] == ["SG-PATH-ESCAPE-001"]
    response = client.post("/api/v1/asp/analyze", json=payload(["cat /opt/rdsocial/config.py"],
        allowed_paths=["relative/**"]))
    assert response.status_code == 422


def test_health_is_public_and_safe() -> None:
    response = client.get("/api/v1/asp/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "scope-guard-asp",
                               "version": "1.0.0-okx", "mode": "read-only"}


def test_openapi_exposes_tool_contract() -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/asp/analyze"]["post"]
    assert operation["operationId"] == "analyze_agent_actions"
    assert operation["requestBody"]["content"]["application/json"]["schema"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]


def test_request_size_limit_is_structured() -> None:
    response = client.post("/api/v1/asp/analyze", content=b"{}",
        headers={"Content-Type": "application/json", "Content-Length": "262145"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_demo_mutations_still_require_demo_auth() -> None:
    assert client.post("/api/tasks", json={"instruction": "a sufficiently long task"}).status_code == 401
    assert client.post("/api/demo/reset").status_code == 401


def test_analysis_does_not_invoke_runner_or_create_task(monkeypatch: Any) -> None:
    before = dict(engine.TASKS)

    async def forbidden(_: str) -> dict[str, Any]:
        raise AssertionError("ASP must not invoke the execution runner")

    async def forbidden_plan(_: object, __: str) -> object:
        raise AssertionError("ASP must not invoke a planner or remote model")

    monkeypatch.setattr(engine.runner, "execute", forbidden)
    monkeypatch.setattr(planner.DemoPlanner, "plan", forbidden_plan)
    monkeypatch.setattr(planner.OpenAIPlanner, "plan", forbidden_plan)
    body = analyze(["cat /opt/rdsocial/config.py"])
    assert body["verdict"] == "ALLOW"
    assert engine.TASKS == before
