# Product decisions

## Decision log

### 2026-07-16 — Deterministic authority

GPT-5.6 proposes task interpretation and boundaries; it does not enforce them. A typed,
deterministic policy engine is the final authority so identical inputs produce identical
decisions and malformed model output cannot expand permissions.

### 2026-07-16 — Synthetic shared server

The MVP uses disposable repository fixtures and isolated containers. This demonstrates
cross-project scope drift without risking a real shared host or production credentials.

### 2026-07-16 — Target and protected validation are separate

Target validation asks whether the requested deployment works. Protected validation asks
whether unrelated resources stayed identical and healthy. A successful target check cannot
substitute for protected integrity evidence.

### 2026-07-16 — Rollback is task-scoped

The runner snapshots and restores only RD Social. Broad environment rollback could damage the
very neighbor Scope Guard is designed to protect. Rollback still rechecks EngageFlow.

### 2026-07-16 — Complement native Codex sandboxing

Native sandboxing constrains technical reach. Scope Guard adds semantic ownership: whether a
reachable file, service, database, port, or domain belongs to the declared task. These layers
are complementary, not competing.

### 2026-07-16 — Unknown resources deny by default

An unregistered resource has no reliable owner or rollback contract. The availability cost of
asking for a clearer manifest is preferable to silent permission expansion.
