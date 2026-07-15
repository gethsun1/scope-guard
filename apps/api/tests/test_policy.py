import pytest
from scope_guard.audit import AuditChain
from scope_guard.command_parser import analyze, normalize_path
from scope_guard.inventory import PROJECTS, resources_for
from scope_guard.models import BoundaryManifest, DecisionType, ProposedAction
from scope_guard.policy import evaluate


def manifest() -> BoundaryManifest:
    return BoundaryManifest(task_id="test", target_project="rdsocial",
        allowed_resources=resources_for(PROJECTS[0]), protected_resources=resources_for(PROJECTS[1]),
        approval_required_resources=[], always_block_rules=["destructive"], created_by="test")


def action(command: str, operation: str = "edit", risk: str = "low") -> ProposedAction:
    return ProposedAction(id="a", sequence=1, command=command, operation_type=operation,
        risk_level=risk, reason="test", expected_effect="test", validation_steps=[], rollback_steps=[])


def test_normalizes_relative_target_path() -> None:
    assert normalize_path("./app.py", "/workspace/projects/rdsocial") == "/workspace/projects/rdsocial/app.py"


def test_rejects_workspace_escape() -> None:
    with pytest.raises(ValueError, match="escapes"):
        normalize_path("../../../../etc/passwd", "/workspace/projects/rdsocial")


@pytest.mark.parametrize("command", ["rm -rf /workspace/projects/rdsocial", "git reset --hard",
    "git clean -fdx", "find /workspace -delete", "echo 'DROP DATABASE engageflow'"])
def test_blocks_destructive_commands(command: str) -> None:
    assert evaluate(action(command), manifest()).decision == DecisionType.BLOCK_DESTRUCTIVE


def test_blocks_protected_service_with_correction() -> None:
    decision = evaluate(action("systemctl restart engageflow-api", "restart", "high"), manifest())
    assert decision.decision == DecisionType.BLOCK_PROTECTED_RESOURCE
    assert decision.suggested_correction == "systemctl restart rdsocial-api"


def test_requires_approval_for_target_restart() -> None:
    decision = evaluate(action("systemctl restart rdsocial-api", "restart", "medium"), manifest())
    assert decision.decision == DecisionType.ALLOW_WITH_APPROVAL


def test_blocks_unknown_resource() -> None:
    assert evaluate(action("systemctl restart generic-api"), manifest()).decision == DecisionType.BLOCK_UNKNOWN_RESOURCE


def test_blocks_secret_and_network_access() -> None:
    secret_decision = evaluate(action("cat /workspace/projects/rdsocial/.env"), manifest())
    assert secret_decision.decision == DecisionType.BLOCK_SECRET_ACCESS
    assert evaluate(action("curl https://evil.test"), manifest()).decision == DecisionType.BLOCK_NETWORK_DESTINATION


def test_parser_extracts_registered_resources() -> None:
    parsed = analyze("systemctl restart rdsocial-api")
    assert [resource.identifier for resource in parsed.resources] == ["rdsocial-api"]


def test_audit_chain_detects_tampering() -> None:
    chain = AuditChain()
    chain.append("t", "one", "tester", {"value": 1})
    chain.append("t", "two", "tester", {"value": 2})
    assert chain.verify()
    chain.events[1].previous_hash = "tampered"
    assert not chain.verify()
