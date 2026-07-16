# Architecture

Scope Guard separates proposal, authority, execution, and evidence.

1. The Next.js control plane collects intent and presents inventory, boundary, approvals,
   live decisions, rollback, audit, and evaluation evidence.
2. FastAPI validates requests, assigns correlation IDs, selects the planner/Codex providers,
   owns process-local task state, and exposes completed audit events as an SSE replay.
3. The planner returns strict `PlannerOutput`. In live mode this uses the OpenAI Responses API;
   demo mode returns deterministic output with the same Pydantic schema.
4. The Codex adapter emits typed `ProposedAction` objects. Policy rejection is recorded and
   returned to the same workflow before the corrected action.
5. Parsing, resource extraction, risk classification, policy evaluation, and execution are
   separate modules. Policy is deterministic and deny-by-default.
6. The runner accepts a fixed operation allowlist. It cannot execute an arbitrary shell,
   access the host Docker socket, or reach external networks.
7. Snapshots store target/protected hashes and state. Rollback restores only RD Social.
8. Every event links to the previous SHA-256 hash. Reports expose audit-chain verification.

## Trust boundaries

```text
Browser | FastAPI | GPT-5.6 | Codex | Policy engine | Runner | Demo apps | Audit store
```

GPT-5.6 and Codex are untrusted proposers. The policy engine is trusted for deterministic
decisions. The runner is trusted only for its small predefined operation implementation. The
synthetic apps and repository content are treated as potentially malicious inputs.

## Docker topology

`sandbox` is an internal network shared by the control API, runner, and two synthetic apps.
Only the control API also joins `control`, which permits publishing port 8000. The runner and
apps have no external network route. Named volumes contain only disposable demo state and
workspace fixtures. All long-running services use UID 10001, read-only roots, `cap_drop: ALL`,
`no-new-privileges`, health checks, and resource limits.
