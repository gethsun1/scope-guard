# Local end-to-end verification

Date: 2026-07-16 (Africa/Nairobi)

## Pre-change baseline

- Ruff passed.
- Pytest passed: 18 tests (one upstream TestClient deprecation warning).
- Frontend tests passed: 3 tests.
- ESLint and TypeScript passed.
- The Next.js production build compiled and generated all then-existing static routes.
- Strict MyPy initially failed in `test_signature_flow.py` because the test returned untyped
  `Response.json()`; the implementation source was clean and the helper is now explicitly cast.

## Docker and signature result

After Docker Desktop was restarted, client 29.6.1, Compose v5.3.0, daemon 29.6.1, and
`hello-world` succeeded. Both Compose configurations validated. A clean-volume demo build reached
healthy state for RD Social, EngageFlow, the runner, and the control API.

The actual failure-injection task produced `ALLOW`, `BLOCK_PROTECTED_RESOURCE`, and
`ALLOW_WITH_APPROVAL`; returned correction `systemctl restart rdsocial-api`; completed target-only
rollback; generated a 20-event report with a valid audit chain; and retained protected hash
`8a8c24fe4a9f1bcb4b7969a7b1809176a8bdd535cb8e14c6bc3c1e2e9e80fdd5`. Reset before and after
both reported protected integrity. No native host execution substituted for the Docker runner.

One Docker CLI invocation later segfaulted while Docker Desktop had stopped. After another
Desktop restart, the full client/daemon/hello-world gate passed and verification resumed.

## Live provider checkpoints

`OPENAI_API_KEY` was unset, so the GPT-5.6 smoke was not executed. The Codex app-server smoke was
executed in read-only, proposal-only mode and succeeded with provider `codex_live`, four typed
proposed actions, and thread `019f6aa3-ad23-7783-b0db-a27b96c43954`. Scope Guard did not execute
those commands.

## Browser result

Playwright Chromium ran in the official container against the Docker API and local Next.js UI.
All six routes passed at 1440×1000 and 390×844 with no horizontal overflow. The six committed
screenshots use actual boundary, block, rollback, report, and benchmark state.
