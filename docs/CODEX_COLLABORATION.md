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

## 2026-07-16 — Phases 3–8: guarded execution safety loop

- Prompt: implement inventory, GPT-5.6 planning, deterministic policy, Codex orchestration,
  snapshots, rollback, audit, streaming events, and reports without weakening Docker isolation.
- Codex work: added the complete typed domain model, registered inventory graph, strict demo
  and live Responses API planners, demo and app-server Codex adapters, structured shell
  analysis, all required policy decisions, approval gates, hash-chained audit events, SSE,
  downloadable JSON/Markdown reports, request correlation, demo authentication, and all
  required task APIs. The control API joins the sandbox only through an internal network;
  the runner remains unable to reach external networks.
- Review/corrections: added token-bound resource matching to prevent `rdsocial` database
  substring collisions with `rdsocial-api`; added non-adjacent `find … -delete` detection;
  corrected the control API network topology so only its public HTTP port is exposed.
- Human decisions: model output may propose and explain but cannot authorize an action.
- Related commit: `feat: integrate codex guarded execution flow`.
- Tests: Ruff and strict MyPy passed; 18 backend unit/integration tests passed; the full
  failure-injection flow ran against real Docker services, blocked EngageFlow, returned a
  correction, required approval, rolled RD Social back, verified audit integrity, and
  produced a downloadable report.

## 2026-07-16 — Phases 9–11: evaluation, UX, and submission

- Prompt: finish the benchmark, polished non-chat interface, security/architecture docs,
  deployment readiness, and hackathon submission material.
- Codex work: built five responsive control-plane routes, explicit demo-provider labels,
  inventory graph, manifest review, blocked-action evidence, approval card, audit timeline,
  report download, and evaluation dashboard. Added 32 SentryBench scenarios and generated
  current JSON/Markdown results. Completed architecture, threat model, product decisions,
  deployment, evaluation, demo script, Devpost draft, and root README.
- Review/corrections: removed external font loading from the interface; tightened unknown
  workspace resource handling; fixed case-normalized recursive permission detection and
  quoted TRUNCATE detection after the first benchmark exposed mismatches.
- Human decisions: hosted writable execution remains optional; local Docker is authoritative.
- Related commits: `test: add sentrybench evaluation suite` and
  `feat: complete execution dashboard`.
- Tests: SentryBench 32/32; Vitest 3/3; ESLint, TypeScript, and Next.js production build pass.

## 2026-07-16 — Phase 12: final verification

- Prompt: complete the original brief and verify the full product without using host execution
  as a sandbox substitute.
- Codex work: ran every available lint, type, unit, integration, evaluation, build, Compose,
  health, hardening, and signature-flow check; recorded the readiness report.
- Review/corrections: resolved a port collision between the two project Compose stacks by
  stopping only the already-running Scope Guard demo before root-stack verification.
- Human decisions: GNU Make was not installed; exact underlying commands were run directly.
- Related commit: `chore: finalize scope guard readiness`.
- Tests: see `docs/FINAL_READINESS.md` for exact outcomes.
