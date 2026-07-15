# Product decisions

## Decision log

### 2026-07-16 — Deterministic authority

GPT-5.6 proposes task interpretation and boundaries; it does not enforce them. A typed,
deterministic policy engine is the final authority so identical inputs produce identical
decisions and malformed model output cannot expand permissions.

### 2026-07-16 — Synthetic shared server

The MVP uses disposable repository fixtures and isolated containers. This demonstrates
cross-project scope drift without risking a real shared host or production credentials.

