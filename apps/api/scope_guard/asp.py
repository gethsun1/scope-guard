import fnmatch
import hashlib
import json
import logging
import posixpath
import re
import time
from datetime import UTC, datetime

from .asp_models import (
    AspActionDecision,
    AspAnalyzeRequest,
    AspAnalyzeResponse,
    AspRequiredApproval,
    AspVerdict,
    AspViolation,
)
from .command_parser import analyze

SERVICE_VERSION = "1.0.0-okx"
POLICY_VERSION = "scope-guard-policy-v1"
MAX_REQUEST_BYTES = 256 * 1024

MUTATING_OPERATIONS = {
    "apply", "chown", "chmod", "cp", "create", "delete", "deploy", "destroy", "install",
    "kill", "migrate", "mkdir", "mv", "patch", "push", "remove", "restart", "rm", "start",
    "stop", "touch", "truncate", "update", "upgrade", "write",
}
READ_ONLY_COMMANDS = {
    "cat", "check-domain", "check-port", "diff", "find", "git", "head", "ls", "pwd", "readlink",
    "rg", "sed", "stat", "tail", "test", "wc",
}
COMMAND_WRAPPERS = {"docker", "kubectl", "npm", "pnpm", "service", "systemctl", "uv"}


def _resource_pattern(resource: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Za-z0-9_.-]){re.escape(resource)}(?![A-Za-z0-9_.-])")


def _normalize_boundary_pattern(pattern: str) -> str:
    if not pattern.startswith("/"):
        raise ValueError("boundary paths must be absolute")
    parts = pattern.split("/")
    if ".." in parts:
        raise ValueError("boundary paths must not contain traversal")
    suffix = "/**" if pattern.endswith("/**") else ""
    base = pattern[:-3] if suffix else pattern
    return posixpath.normpath(base) + suffix


def _normalize_action_path(path: str) -> str:
    if not path.startswith("/") or ".." in path.split("/"):
        raise ValueError("action paths must be absolute and must not contain traversal")
    return posixpath.normpath(path)


def _path_matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        root = pattern[:-3].rstrip("/") or "/"
        return path == root or path.startswith(root + "/")
    return fnmatch.fnmatchcase(path, pattern)


def _operation(tokens: list[str]) -> tuple[str, bool, bool]:
    lowered = [token.lower() for token in tokens]
    if not lowered:
        return "unknown", False, False
    command = posixpath.basename(lowered[0])
    if command in COMMAND_WRAPPERS:
        operation = next((token for token in lowered[1:] if not token.startswith("-")), "unknown")
        if command in {"npm", "pnpm", "uv"} and operation in {"test", "lint", "typecheck", "run"}:
            return operation, False, True
        return operation, operation in MUTATING_OPERATIONS, operation != "unknown"
    if command == "git":
        operation = next((token for token in lowered[1:]
                          if not token.startswith("-") and not token.startswith("/")), "unknown")
        readonly = operation in {"branch", "diff", "log", "show", "status"}
        return operation, not readonly, readonly or operation in MUTATING_OPERATIONS
    return command, command in MUTATING_OPERATIONS, command in READ_ONLY_COMMANDS or command in MUTATING_OPERATIONS


def _decision(action: str, request: AspAnalyzeRequest) -> AspActionDecision:
    parsed = analyze(action)
    tokens = parsed.tokens
    operation, mutation, recognized = _operation(tokens)
    allowed_patterns = [_normalize_boundary_pattern(value) for value in request.allowed_paths]
    protected_patterns = [_normalize_boundary_pattern(value) for value in request.protected_paths]
    matched_allowed_resources = [
        value for value in request.allowed_resources if _resource_pattern(value).search(action)
    ]
    matched_protected_resources = [
        value for value in request.protected_resources if _resource_pattern(value).search(action)
    ]
    raw_paths = [
        token for token in tokens
        if token.startswith(("/", "./", "../")) and not token.startswith(("http://", "https://"))
    ]
    normalized_paths: list[str] = []
    try:
        normalized_paths = [_normalize_action_path(path) for path in raw_paths]
    except ValueError:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="critical",
            reason="The action contains a path traversal or a path outside the absolute boundary model.",
            matched_resources=matched_allowed_resources + matched_protected_resources,
            matched_paths=[], policy_codes=["SG-PATH-ESCAPE-001"])
    matched_protected_paths = [
        path for path in normalized_paths if any(_path_matches(path, pattern) for pattern in protected_patterns)
    ]
    matched_allowed_paths = [
        path for path in normalized_paths if any(_path_matches(path, pattern) for pattern in allowed_patterns)
    ]
    unmatched_paths = [path for path in normalized_paths if path not in matched_protected_paths + matched_allowed_paths]

    destructive = [value for value in parsed.dangerous_patterns if value != "path_escape"]
    if destructive:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="critical",
            reason="The action contains a destructive operation that is always blocked.",
            matched_resources=matched_allowed_resources + matched_protected_resources,
            matched_paths=matched_allowed_paths + matched_protected_paths,
            policy_codes=["SG-DESTRUCTIVE-001"])
    if parsed.secret_access:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="critical",
            reason="The action attempts to read secret material.",
            matched_resources=matched_allowed_resources + matched_protected_resources,
            matched_paths=matched_allowed_paths + matched_protected_paths, policy_codes=["SG-SECRET-001"])
    if matched_protected_resources:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="critical",
            reason="The action targets an explicitly protected resource.",
            matched_resources=matched_protected_resources, matched_paths=matched_protected_paths,
            policy_codes=["SG-PROTECTED-001", "PROTECTED_RESOURCE_ACCESS"])
    if matched_protected_paths:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="critical",
            reason="The action targets an explicitly protected path.", matched_resources=[],
            matched_paths=matched_protected_paths, policy_codes=["SG-PROTECTED-001", "PROTECTED_PATH_ACCESS"])
    if unmatched_paths:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="high",
            reason="The action references a path outside the approved scope.",
            matched_resources=matched_allowed_resources, matched_paths=unmatched_paths,
            policy_codes=["SG-UNKNOWN-002", "PATH_OUTSIDE_APPROVED_SCOPE"])
    if not recognized or parsed.ambiguous:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="high",
            reason="The action is unknown or cannot be evaluated unambiguously.",
            matched_resources=matched_allowed_resources, matched_paths=matched_allowed_paths,
            policy_codes=["SG-AMBIGUITY-001" if parsed.ambiguous else "SG-UNKNOWN-001"])
    if not matched_allowed_resources and not matched_allowed_paths:
        return AspActionDecision(action=action, verdict=AspVerdict.BLOCK, risk_level="high",
            reason="The action references no explicitly allowed resource; unknown resources are denied.",
            matched_resources=[], matched_paths=[], policy_codes=["SG-UNKNOWN-001"])
    if mutation:
        return AspActionDecision(action=action, verdict=AspVerdict.REQUIRE_APPROVAL, risk_level="medium",
            reason=f"The allowed {operation} mutation requires explicit approval.",
            matched_resources=matched_allowed_resources, matched_paths=matched_allowed_paths,
            policy_codes=["SG-APPROVAL-001", "MUTATION_REQUIRES_APPROVAL"])
    return AspActionDecision(action=action, verdict=AspVerdict.ALLOW, risk_level="low",
        reason="The read-only action references only explicitly allowed scope.",
        matched_resources=matched_allowed_resources, matched_paths=matched_allowed_paths,
        policy_codes=["SG-SCOPE-ALLOW"])


def _risk(decision: AspActionDecision) -> int:
    if "SG-DESTRUCTIVE-001" in decision.policy_codes or "SG-SECRET-001" in decision.policy_codes:
        return 100
    if decision.verdict == AspVerdict.BLOCK and decision.risk_level == "critical":
        return 95
    if decision.verdict == AspVerdict.BLOCK:
        return 85
    if decision.verdict == AspVerdict.REQUIRE_APPROVAL:
        return 60
    return 10


def evaluate_asp_request(request: AspAnalyzeRequest) -> AspAnalyzeResponse:
    started = time.perf_counter()
    decisions = [_decision(action, request) for action in request.proposed_actions]
    if any(item.verdict == AspVerdict.BLOCK for item in decisions):
        verdict = AspVerdict.BLOCK
    elif any(item.verdict == AspVerdict.REQUIRE_APPROVAL for item in decisions):
        verdict = AspVerdict.REQUIRE_APPROVAL
    else:
        verdict = AspVerdict.ALLOW
    violations = [
        AspViolation(code=item.policy_codes[-1], action_index=index, reason=item.reason)
        for index, item in enumerate(decisions) if item.verdict == AspVerdict.BLOCK
    ]
    approvals = [
        AspRequiredApproval(action_index=index, reason="Approved-scope mutation")
        for index, item in enumerate(decisions) if item.verdict == AspVerdict.REQUIRE_APPROVAL
    ]
    corrections = [
        f"Remove or replace action {item.action!r} so it references only explicitly allowed scope."
        for item in decisions if item.verdict == AspVerdict.BLOCK
    ]
    summaries = {
        AspVerdict.BLOCK: f"{len(violations)} proposed action(s) violated the approved boundary.",
        AspVerdict.REQUIRE_APPROVAL: f"{len(approvals)} proposed action(s) require explicit approval.",
        AspVerdict.ALLOW: "All proposed actions are read-only and within the explicitly allowed scope.",
    }
    risk_score = max(_risk(item) for item in decisions)
    material = {
        "request": request.model_dump(mode="json", exclude_none=True),
        "verdict": verdict,
        "risk_score": risk_score,
        "decisions": [item.model_dump(mode="json") for item in decisions],
        "policy_version": POLICY_VERSION,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")).hexdigest()
    evaluation_id = f"sg_eval_{digest[:24]}"
    response = AspAnalyzeResponse(service_version=SERVICE_VERSION, evaluation_id=evaluation_id,
        verdict=verdict, risk_score=risk_score, summary=summaries[verdict], decisions=decisions,
        violations=violations, required_approvals=approvals, recommended_corrections=corrections,
        policy_version=POLICY_VERSION, evidence_hash=f"sha256:{digest}", evaluated_at=datetime.now(UTC))
    logging.info("asp_evaluation id=%s verdict=%s duration_ms=%.3f actions=%d violations=%d approvals=%d",
        evaluation_id, verdict, (time.perf_counter() - started) * 1000, len(decisions), len(violations),
        len(approvals))
    return response
