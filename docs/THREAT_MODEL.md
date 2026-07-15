# Threat model

## Assets

Approved task boundaries, target source/state, protected project integrity, credentials,
audit evidence, and rollback snapshots.

## Threats and controls

| Threat | Control | Residual risk |
|---|---|---|
| Scope drift / cross-project access | Resource ownership, protected manifest, deterministic block | Incomplete inventory can misclassify; unknowns deny |
| Prompt injection / malicious repository instructions | Model cannot authorize; manifest immutable during execution | Social engineering before human approval |
| Command injection | Structured parsing and predefined runner operations | Parser subset requires continued fuzzing |
| Path traversal / symlink escape | Normalize beneath `/workspace`; runner has no host mounts | Future filesystem executor must use descriptor-safe traversal |
| Secret exposure | Secret patterns blocked; no credentials in demo runner | Live adapters need centralized redaction |
| Network exfiltration | Network destinations denied; runner network is Docker-internal | Control API has normal outbound access for live APIs |
| Privilege escalation | UID 10001, capabilities dropped, no-new-privileges, read-only root | Container runtime vulnerabilities remain platform risk |
| Audit tampering | Previous-hash chain verified in reports | In-memory chain needs durable signing/anchoring in production |
| Rollback abuse | Snapshot required; rollback operation is target-only | Snapshot authorization needs durable identity in production |
| Model hallucination / compromised agent output | Pydantic validation; deterministic final authority | Misleading explanations may still require review |
| Unknown-resource ambiguity | Deny unknown and ambiguous resources | Availability cost from conservative false positives |
| Shared proxy/config modification | Unregistered workspace resources deny | Explicit shared-resource workflows need approval policy |

## Trust boundaries

- **User → frontend:** local demo identity is not production authentication.
- **Frontend → orchestrator:** state-changing calls require the local demo token.
- **Orchestrator → GPT-5.6/Codex:** no secrets; outputs are untrusted typed proposals.
- **Codex → policy:** no action bypass exists in the orchestration path.
- **Policy → runner:** only allowed/approved actions become predefined operations.
- **Runner → synthetic environment:** internal network and disposable named volumes only.
- **Orchestrator → audit:** append-only semantics and hash linkage; durable signing is future work.

## Security invariants

Unknown resources deny; no implicit permission expansion; protected verification is distinct
from target validation; rollback never touches EngageFlow; the model is never final authority;
no host root, Docker socket, SSH key, or production credential enters the runner.

