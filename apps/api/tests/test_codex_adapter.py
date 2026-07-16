import json
from typing import Any

import pytest
from scope_guard.codex import CodexAppServerAdapter, DemoCodexAdapter
from scope_guard.inventory import PROJECTS, resources_for
from scope_guard.models import BoundaryManifest, ProposedActionSet, strict_json_schema


def manifest() -> BoundaryManifest:
    return BoundaryManifest(task_id="task-1", target_project="rdsocial",
        allowed_resources=resources_for(PROJECTS[0]), protected_resources=resources_for(PROJECTS[1]),
        approval_required_resources=[], always_block_rules=["protected_resource"],
        created_by="test", approved_by="tester")


def action_payload(command: str = "systemctl restart rdsocial-api") -> str:
    return json.dumps({"actions": [{"id": "restart-rdsocial", "sequence": 1,
        "command": command, "operation_type": "restart", "risk_level": "medium",
        "reason": "Restart target service", "expected_effect": "Target restart",
        "validation_steps": ["health"], "rollback_steps": ["restore"]}]})


@pytest.mark.asyncio
async def test_demo_adapter_remains_deterministic() -> None:
    adapter = DemoCodexAdapter()
    assert [item.id for item in await adapter.actions()] == [
        "edit-rdsocial", "unsafe-engageflow", "restart-rdsocial"]
    assert adapter.provider == "codex_demo"


@pytest.mark.asyncio
async def test_live_adapter_maps_events_and_persists_session() -> None:
    calls: list[tuple[str, str | None]] = []

    async def runner(prompt: str, thread_id: str | None,
                     schema: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
        calls.append((prompt, thread_id))
        assert schema == strict_json_schema(ProposedActionSet)
        return "thread-123", action_payload(), [{"method": "turn/started"},
                                                  {"method": "item/completed"}]

    mapped: list[str] = []

    async def sink(name: str, event: dict[str, Any]) -> None:
        mapped.append(name)

    adapter = CodexAppServerAdapter(runner=runner)
    actions = await adapter.actions("deploy target", [], manifest(), sink)
    corrected = await adapter.rejection_feedback({"decision": "BLOCK_PROTECTED_RESOURCE"}, sink)
    assert actions[0].command == corrected[0].command
    assert calls[0][1] is None
    assert calls[1][1] == "thread-123"
    assert adapter.thread_id == "thread-123"
    assert mapped == ["turn/started", "item/completed"] * 2
    assert "Do not dispute or bypass" in calls[1][0]


@pytest.mark.asyncio
async def test_live_adapter_rejects_malformed_actions() -> None:
    async def runner(prompt: str, thread_id: str | None,
                     schema: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
        return "thread-123", '{"actions": []}', []

    with pytest.raises(ValueError, match="malformed proposed actions"):
        await CodexAppServerAdapter(runner=runner).actions("deploy", [], manifest())


@pytest.mark.asyncio
async def test_rejection_requires_existing_session() -> None:
    with pytest.raises(RuntimeError, match="has not been started"):
        await CodexAppServerAdapter().rejection_feedback({"decision": "BLOCK"})
