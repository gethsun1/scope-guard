# Codex collaboration log

This file records the actual build history. It does not claim live model actions that did
not occur.

## 2026-07-16 — Phase 0: workspace preflight

- Prompt: build the complete Scope Guard hackathon MVP in sequenced phases.
- Codex work: confirmed the workspace was an empty Git repository; checked Node, pnpm,
  Python, uv, and Docker CLI availability; added repository safety instructions, ignore
  rules, initial product README, and the decision log.
- Review/corrections: Docker CLI segfaulted during its version check; container execution
  remains to be verified separately, and no external Docker state was inspected.
- Human decisions: supplied product brief and mandatory safety boundary.
- Related commit: `chore: initialize scope guard workspace`.
- Tests: workspace/preflight inspection only.

## 2026-07-16 — Phase 1: monorepo foundation

- Prompt: resume the paused foundation after verifying repaired Docker Desktop and preserve
  all existing Phase 1 work.
- Codex work: scaffolded the pnpm/uv monorepo, FastAPI health service, Next.js App Router
  shell, strict TypeScript and Python tooling, CI, Make targets, environment template, and
  production multi-stage images. Both runtime images use UID 10001, drop all capabilities,
  prohibit privilege escalation, use read-only roots, and apply CPU/memory limits.
- Review/corrections: corrected the web bind address and IPv4 health check; pinned direct
  ESLint plugins to the Next.js version; excluded generated build output from lint and the
  Docker build context. No host socket or host filesystem is mounted.
- Human decisions: repaired and restarted Docker Desktop/WSL; retained repository-local
  author `Gethsun1 <gethsun09@gmail.com>`.
- Related commit: `feat: scaffold control plane monorepo`.
- Tests: Ruff passed; ESLint passed; strict TypeScript passed; Next.js production build
  passed; Compose configuration passed; API and web containers both reached healthy state.

## 2026-07-16 — Phase 2: synthetic shared server

- Prompt: continue with the isolated Docker demonstration; never substitute host execution.
- Codex work: created independent RD Social and EngageFlow health services and a restricted
  runner that accepts only six predefined state operations. Added non-root image-owned
  volume initialization, internal-only networking, read-only roots, dropped capabilities,
  resource limits, baseline inventory, and deterministic reset.
- Review/corrections: initial named-volume seeding failed under UID 10001. Replaced bind-copy
  initialization with Docker volume copy-up from a non-root-owned initializer image; no
  elevation or host mount was introduced.
- Human decisions: required Docker as a hard dependency for the signature demonstration.
- Related commit: `feat: add synthetic shared-server environment`.
- Tests: all three long-running demo containers reached healthy state; the runner blocked an
  unknown EngageFlow restart with HTTP 403; deploy, migration, deliberate failure, and
  rollback executed in-container; EngageFlow retained the same SHA-256 hash and healthy
  state throughout; RD Social returned exactly to its pre-mutation hash after rollback.
