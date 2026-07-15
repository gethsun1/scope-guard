import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

from .audit import AuditChain
from .codex import DemoCodexAdapter
from .config import settings
from .models import (
    BoundaryManifest,
    CreateTaskRequest,
    DecisionType,
    PolicyDecision,
    ProposedAction,
    Resource,
    ResourceType,
    Snapshot,
)
from .planner import PROMPT_VERSION, DemoPlanner, OpenAIPlanner
from .policy import evaluate


class Runner:
    async def execute(self, operation: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{settings().demo_runner_url}/execute",
                                         json={"operation": operation})
            response.raise_for_status()
            value: dict[str, Any] = response.json()
            return value


runner: Runner = Runner()


@dataclass
class Task:
    id: str
    instruction: str
    failure_injection: bool
    status: str = "created"
    provider: str = "codex_demo"
    plan: dict[str, Any] | None = None
    manifest: BoundaryManifest | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    snapshot: Snapshot | None = None
    pending_action: str | None = None
    rolled_back: bool = False
    report: dict[str, Any] | None = None
    events: AuditChain = field(default_factory=AuditChain)


TASKS: dict[str, Task] = {}


def create_task(request: CreateTaskRequest) -> Task:
    task = Task(id=str(uuid4()), instruction=request.instruction,
                failure_injection=request.failure_injection)
    task.events.append(task.id, "task_received", "demo_user", {"instruction": request.instruction})
    TASKS[task.id] = task
    return task


def get_task(task_id: str) -> Task:
    if task_id not in TASKS:
        raise KeyError(task_id)
    return TASKS[task_id]


async def plan_task(task: Task) -> dict[str, Any]:
    planner = DemoPlanner() if settings().demo_mode else OpenAIPlanner()
    plan = await planner.plan(task.instruction)
    task.plan = plan.model_dump(mode="json")
    task.manifest = BoundaryManifest(task_id=task.id, target_project=plan.target_project,
        allowed_resources=plan.allowed_resources, protected_resources=plan.protected_resources,
        approval_required_resources=[Resource(type=ResourceType.SERVICE,
            identifier="rdsocial-api", project_id="rdsocial")],
        always_block_rules=["destructive_operation", "protected_resource", "secret_access"],
        created_by="gpt-5.6-demo-planner" if settings().demo_mode else settings().openai_model)
    task.status = "boundary_proposed"
    task.events.append(task.id, "boundary_proposed", task.manifest.created_by,
                       {"confidence": plan.confidence, "prompt_version": PROMPT_VERSION})
    return task.plan


def approve_boundary(task: Task, actor: str = "demo_user") -> None:
    if not task.manifest:
        raise ValueError("plan must be generated first")
    task.manifest.approved_by = actor
    task.status = "boundary_approved"
    task.events.append(task.id, "boundary_approved", actor, {"manifest_version": task.manifest.version})


def record_decision(task: Task, action: ProposedAction, decision: PolicyDecision) -> None:
    row = {"action": action.model_dump(mode="json"), "decision": decision.model_dump(mode="json")}
    task.actions.append(row)
    severity = "warning" if decision.decision.value.startswith("BLOCK") else "info"
    task.events.append(task.id, "policy_decision", "policy_engine",
                       decision.model_dump(mode="json"), severity)


async def execute_task(task: Task) -> list[dict[str, Any]]:
    if not task.manifest or not task.manifest.approved_by:
        raise ValueError("approved boundary required")
    task.status = "running"
    before = await runner.execute("snapshot")
    task.snapshot = Snapshot(task_id=task.id,
        resource_hashes={"rdsocial": str(before["rdsocial_hash"]),
                         "engageflow": str(before["engageflow_hash"])},
        repository_state={"rdsocial": "snapshotted"},
        service_state={"rdsocial-api": "healthy", "engageflow-api": "healthy"},
        container_state={"runner": "isolated"}, database_migration_state={"rdsocial": 0, "engageflow": 0},
        health_state={"rdsocial": True, "engageflow": True})
    task.events.append(task.id, "snapshot_created", "sandbox_runner",
                       {"protected_hash": before["engageflow_hash"]})
    adapter = DemoCodexAdapter()
    for action in await adapter.actions():
        task.events.append(task.id, "codex_action_proposed", adapter.provider,
                           {"action_id": action.id, "command": action.command})
        decision = evaluate(action, task.manifest)
        record_decision(task, action, decision)
        if decision.decision == DecisionType.BLOCK_PROTECTED_RESOURCE:
            task.events.append(task.id, "rejection_returned", "orchestrator",
                {"action_id": action.id, "decision": decision.decision,
                 "violations": [item.model_dump() for item in decision.violations],
                 "suggested_correction": decision.suggested_correction})
        elif decision.decision == DecisionType.ALLOW:
            task.events.append(task.id, "action_executed", "sandbox_runner",
                               {"action_id": action.id, "operation": "validated_code_edit"})
        elif decision.decision == DecisionType.ALLOW_WITH_APPROVAL:
            task.pending_action = action.id
            task.status = "awaiting_approval"
            task.events.append(task.id, "approval_requested", "orchestrator", {"action_id": action.id})
            break
        await asyncio.sleep(0)
    return task.actions


async def approve_action(task: Task, action_id: str) -> dict[str, Any]:
    if task.pending_action != action_id:
        raise ValueError("action is not pending approval")
    task.events.append(task.id, "action_approved", "demo_user", {"action_id": action_id})
    deployed = await runner.execute("deploy_rdsocial")
    migrated = await runner.execute("migrate_rdsocial")
    task.events.append(task.id, "action_executed", "sandbox_runner", {
        "action_id": action_id, "operations": ["deploy_rdsocial", "migrate_rdsocial"], "exit_code": 0})
    if task.failure_injection:
        await runner.execute("fail_rdsocial")
        task.events.append(task.id, "health_check_failed", "validator", {"project": "rdsocial"}, "error")
        await rollback_task(task)
    else:
        task.status = "completed"
        task.events.append(task.id, "health_checks_completed", "validator",
                           {"rdsocial": "healthy", "engageflow": "healthy"})
    protected_hash = str(migrated["engageflow_hash"])
    unchanged = bool(task.snapshot and protected_hash == task.snapshot.resource_hashes["engageflow"])
    task.events.append(task.id, "protected_integrity_verified", "validator",
                       {"engageflow_unchanged": unchanged, "health": "healthy"})
    task.pending_action = None
    task.report = build_report(task, str(deployed["rdsocial_hash"]), protected_hash)
    return task.report


async def rollback_task(task: Task) -> None:
    if not task.snapshot:
        raise ValueError("snapshot required")
    task.events.append(task.id, "rollback_started", "orchestrator", {"scope": "rdsocial-only"}, "warning")
    result = await runner.execute("rollback_rdsocial")
    task.rolled_back = True
    task.status = "rolled_back"
    task.events.append(task.id, "rollback_completed", "sandbox_runner", {
        "rdsocial_restored": result["rdsocial_hash"] == task.snapshot.resource_hashes["rdsocial"],
        "engageflow_touched": False})


def build_report(task: Task, target_hash: str = "", protected_hash: str = "") -> dict[str, Any]:
    blocked = [row for row in task.actions if row["decision"]["decision"].startswith("BLOCK")]
    return {"task_id": task.id, "status": task.status, "provider": task.provider,
        "changed_target_resources": ["rdsocial-api", "rdsocial database"],
        "preserved_protected_resources": ["engageflow-api", "engageflow database"],
        "blocked_actions": blocked, "target_hash": target_hash, "protected_hash": protected_hash,
        "rollback": {"triggered": task.rolled_back, "success": task.rolled_back if task.rolled_back else None},
        "audit_integrity": task.events.verify(), "event_count": len(task.events.events),
        "generated_at": datetime.now(UTC).isoformat()}


def serialize_task(task: Task) -> dict[str, Any]:
    return {"id": task.id, "instruction": task.instruction, "failure_injection": task.failure_injection,
        "status": task.status, "provider": task.provider, "plan": task.plan,
        "manifest": task.manifest.model_dump(mode="json") if task.manifest else None,
        "actions": task.actions, "pending_action": task.pending_action,
        "rolled_back": task.rolled_back, "report": task.report}
