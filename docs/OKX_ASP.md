# Scope Guard OKX.AI Agent Service Provider

Scope Guard exposes a free, read-only Agent-to-MCP (A2MCP) service that evaluates proposed
AI-agent actions before execution. It returns a deterministic `ALLOW`, `BLOCK`, or
`REQUIRE_APPROVAL` verdict and **never executes the submitted actions**.

The original Scope Guard control plane, deterministic policy engine, Devpost application, and
synthetic RD Social/EngageFlow demonstration predate the OKX.AI adaptation. During the OKX.AI
Genesis work, the project added the generic request boundary, stateless aggregation, evidence
hash, public ASP routes, validation, safety tests, OpenAPI contract, and this documentation.

## Why A2MCP

The capability takes bounded structured parameters and immediately returns a machine-readable,
verifiable result. It requires neither negotiation nor asynchronous delivery, making A2MCP the
appropriate OKX.AI mode. The initial service is free (`price: 0`) and does not use x402,
blockchain transactions, or a smart contract.

## Public interface

- `GET /api/v1/asp/health`
- `POST /api/v1/asp/analyze`
- Content type: `application/json`
- Authentication: none for these two read-only routes
- Service version: `1.0.0-okx`
- Maximum request body: 256 KiB when `Content-Length` is present
- Analysis timeout: two seconds

The endpoint is independent of `X-Demo-Token`. Existing Devpost mutation routes remain protected
by that token.

## Request

The request contains a task, 1–25 proposed action strings, explicit allowed/protected resources
and paths, a risk tolerance enum (`strict`, `balanced`, or `permissive`), and optional bounded
JSON metadata. Strings, lists, metadata depth, Unicode, null bytes, path form, and overlapping
boundaries are validated. Unexpected fields are rejected.

```json
{
  "task": "Deploy RD Social without modifying EngageFlow",
  "proposed_actions": ["systemctl restart engageflow-api", "systemctl restart rdsocial-asgi"],
  "allowed_resources": ["rdsocial-asgi"],
  "protected_resources": ["engageflow-api"],
  "allowed_paths": ["/opt/rdsocial/**"],
  "protected_paths": ["/opt/engageflow/**"],
  "risk_tolerance": "strict",
  "metadata": {"agent": "codex", "environment": "production"}
}
```

## Response and verdict semantics

The response includes an evaluation ID, overall verdict, deterministic risk score, per-action
decisions, violations, approvals, corrections, policy version, canonical SHA-256 evidence hash,
and evaluation time. Overall precedence is `BLOCK` > `REQUIRE_APPROVAL` > `ALLOW`.

The evidence hash covers the normalized material request, decisions, overall verdict, risk score,
and policy version. It intentionally excludes `evaluated_at`; identical material input therefore
produces the same decisions, score, evaluation ID, and evidence hash.

Risk scores are fixed policy values: 100 for destructive or secret access; 95 for critical
protected-boundary/path-escape blocks; 85 for unknown, ambiguous, or out-of-scope blocks; 60 for
an allowed mutation requiring approval; and 10 for an allowed read-only action.

## Policy codes

Existing codes are retained: `SG-DESTRUCTIVE-001`, `SG-SECRET-001`, `SG-PROTECTED-001`,
`SG-AMBIGUITY-001`, `SG-UNKNOWN-001`, `SG-UNKNOWN-002`, `SG-APPROVAL-001`, and
`SG-SCOPE-ALLOW`.

Public adapter codes add detail without changing the Devpost policy:
`PROTECTED_RESOURCE_ACCESS`, `PROTECTED_PATH_ACCESS`, `PATH_OUTSIDE_APPROVED_SCOPE`,
`MUTATION_REQUIRES_APPROVAL`, and `SG-PATH-ESCAPE-001`.

Unknown resources and paths are denied. Destructive operations, secret access, protected scope,
malformed shell text, path traversal, and ambiguous actions block. Allowed mutations require
approval. Only recognized, read-only actions wholly inside allowed scope receive `ALLOW`.

## Safety model and limitations

Analysis is bounded, in-memory, and stateless. The ASP imports no runner, Docker client, database,
planner, Codex adapter, or network client. It does not create task or audit records, write files,
make network calls, or persist submitted content. Logs contain only evaluation ID, verdict,
duration, and aggregate counts.

The parser supports a conservative command subset rather than a complete shell AST. It matches
caller-declared resource identifiers literally and supports absolute POSIX paths and glob-style
boundaries. Unrecognized actions fail closed. Risk tolerance is material input but never weakens
deny-by-default or approval policy.

## curl example

```bash
curl -i -X POST "$SCOPE_GUARD_API_URL/api/v1/asp/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Deploy RD Social without modifying EngageFlow",
    "proposed_actions": [
      "systemctl restart engageflow-api",
      "systemctl restart rdsocial-asgi"
    ],
    "allowed_resources": ["rdsocial-asgi"],
    "protected_resources": ["engageflow-api"],
    "allowed_paths": ["/opt/rdsocial/**"],
    "protected_paths": ["/opt/engageflow/**"],
    "risk_tolerance": "strict"
  }'
```

## Railway verification

```bash
curl --fail "$SCOPE_GUARD_API_URL/api/v1/asp/health"
curl --fail -X POST "$SCOPE_GUARD_API_URL/api/v1/asp/analyze" \
  -H 'Content-Type: application/json' --data @request.json
```

The expected valid-call response is HTTP 200 JSON without a login redirect or authentication
challenge. Roll back by redeploying the previous known-good Scope Guard Railway deployment.

## OKX.AI registration metadata

- ASP type: `A2MCP`
- Service name: `Scope Guard Agent Safety`
- Description: `Deterministically analyzes proposed AI-agent commands and infrastructure actions before execution, returning ALLOW, BLOCK, or REQUIRE_APPROVAL without executing them.`
- Price: `0` (free)
- Endpoint: `https://scopeguard-api-production.up.railway.app/api/v1/asp/analyze`
