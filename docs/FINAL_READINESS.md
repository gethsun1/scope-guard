# Final readiness report

Date: 2026-07-16 (Africa/Nairobi)

## Status

Judge-ready local MVP. Demo mode is operational without credentials. The live OpenAI Responses
API planner is implemented and credential-gated but was not smoke-tested here. The read-only,
proposal-only live Codex app-server smoke succeeded; demo mode remains the reproducible default.

## Verification

- Ruff: passed
- MyPy strict: passed, 16 source files
- Backend: 30 passed (one upstream TestClient deprecation warning)
- Frontend: 4 passed
- ESLint: passed
- TypeScript: passed
- Next.js: production build includes six product routes plus framework not-found handling
- Root Compose: API and web images built; both health checks passed
- Demo Compose: clean-volume reset and all four long-running services passed health checks
- Runner hardening: UID/GID 10001, `CapEff=0`, `NoNewPrivs=1`
- Signature failure flow: protected restart blocked; correction returned; target approval
  required; failure injected; rollback succeeded; audit chain valid; EngageFlow healthy
- SentryBench: 32/32 expected decisions; 100% unsafe detection; 100% safe acceptance; 0%
  false-positive and false-negative rates; 100% protected integrity and rollback success;
  measured average policy latency is recorded in the generated result file; rollback is reported
  separately because SentryBench does not execute it
- Playwright: all six routes passed at desktop and mobile widths; six real-state screenshots

## Environment limitation

GNU Make is not installed in the verification WSL environment, so every Make target's
underlying command was run directly. The Makefile is present for environments with GNU Make.

## Remaining production work

Durable task/audit persistence, production identity, hosted URLs, demo video, GPT credentialed
smoke evidence, and production secret/configuration setup.

## Safety statement

Only files and Scope Guard Docker resources inside this repository were used. No unrelated
project, production service, database, reverse proxy, SSH configuration, or infrastructure was
inspected or modified. RD Social and EngageFlow were exclusively synthetic repository assets.
