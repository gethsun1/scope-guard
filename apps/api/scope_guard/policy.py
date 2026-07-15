from .command_parser import analyze
from .models import BoundaryManifest, DecisionType, PolicyDecision, ProposedAction, Violation


def _decision(action: ProposedAction, decision: DecisionType, rule: str, explanation: str,
              violations: list[Violation], resources: list[dict[str, object]],
              correction: str | None = None) -> PolicyDecision:
    return PolicyDecision(action_id=action.id, decision=decision, matched_rules=[rule],
        violations=violations, human_explanation=explanation,
        machine_explanation={"decision": decision, "rule": rule, "resources": resources,
                             "risk": action.risk_level}, suggested_correction=correction)


def evaluate(action: ProposedAction, manifest: BoundaryManifest) -> PolicyDecision:
    parsed = analyze(action.command, action.working_directory)
    resources = [resource.model_dump(mode="json") for resource in parsed.resources]
    if parsed.dangerous_patterns:
        return _decision(action, DecisionType.BLOCK_DESTRUCTIVE, "SG-DESTRUCTIVE-001",
            "The command contains a destructive operation that is always blocked.",
            [Violation(rule="SG-DESTRUCTIVE-001", detail=", ".join(parsed.dangerous_patterns))], resources)
    if parsed.secret_access:
        return _decision(action, DecisionType.BLOCK_SECRET_ACCESS, "SG-SECRET-001",
            "Reading secret material is outside this task boundary.",
            [Violation(rule="SG-SECRET-001", detail="Secret-reading pattern detected")], resources)
    if parsed.network_destination:
        return _decision(action, DecisionType.BLOCK_NETWORK_DESTINATION, "SG-NETWORK-001",
            "The outbound network destination is not approved.",
            [Violation(rule="SG-NETWORK-001", resource=parsed.network_destination,
                       detail="Unapproved outbound destination")], resources)
    protected = next((resource for resource in parsed.resources if resource.protected or
                      resource.project_id == "engageflow"), None)
    if protected:
        correction = action.command.replace("engageflow", "rdsocial").replace("8201", "8101")
        return _decision(action, DecisionType.BLOCK_PROTECTED_RESOURCE, "SG-PROTECTED-001",
            f"{protected.identifier} belongs to EngageFlow, which is protected by the approved task boundary.",
            [Violation(rule="SG-PROTECTED-001", resource=protected.identifier,
                       detail="Protected EngageFlow resource")], resources, correction)
    if parsed.ambiguous:
        return _decision(action, DecisionType.BLOCK_POLICY_AMBIGUITY, "SG-AMBIGUITY-001",
            "Shell composition makes the affected resource boundary ambiguous.",
            [Violation(rule="SG-AMBIGUITY-001", detail="Ambiguous composed shell command")], resources)
    if not parsed.resources:
        return _decision(action, DecisionType.BLOCK_UNKNOWN_RESOURCE, "SG-UNKNOWN-001",
            "The command references no registered resource; unknown resources are denied.",
            [Violation(rule="SG-UNKNOWN-001", detail="No registered resource resolved")], resources)
    if any(resource.project_id not in {manifest.target_project, None} for resource in parsed.resources):
        return _decision(action, DecisionType.BLOCK_OUT_OF_SCOPE, "SG-SCOPE-001",
            "The action references a resource outside the approved target project.",
            [Violation(rule="SG-SCOPE-001", detail="Non-target project reference")], resources)
    if action.risk_level in {"medium", "high"} or action.operation_type in {"restart", "migration"}:
        return _decision(action, DecisionType.ALLOW_WITH_APPROVAL, "SG-APPROVAL-001",
            "The action is in scope, but this mutation requires human approval.", [], resources)
    return _decision(action, DecisionType.ALLOW, "SG-SCOPE-ALLOW",
        "The action references only resources allowed by the approved boundary.", [], resources)

