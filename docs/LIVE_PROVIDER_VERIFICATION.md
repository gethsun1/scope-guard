# Live provider verification

## GPT-5.6 live adapter

- Provider: `gpt_live`; configured model: `gpt-5.6`; prompt version: `scope-guard-planner-v1`.
- The Responses API adapter requests strict JSON Schema output and validates the response with
  Pydantic before creating any boundary. Model output cannot authorize execution.
- On 2026-07-16, a manual smoke request using the developer-provided local credential reached
  OpenAI but returned HTTP 429 `insufficient_quota`. No structured result, target-project result,
  or resource counts were produced, so the live GPT smoke **did not pass**.
- The credential was not printed, logged, committed, or uploaded to the hosted demo. Retry is a
  developer-only action after API billing/quota is available.

## Codex live adapter

- Provider: `codex_live`; proposal smoke thread: `019f6aa3-ad23-7783-b0db-a27b96c43954`.
- The smoke verified app-server startup, read-only proposal generation, schema validation, four
  typed proposed actions, and thread ID capture.
- It was proposal-only. It did not execute the full guarded Docker workflow or prove a hosted
  live-provider deployment. The deterministic `codex_demo` adapter drives the reproducible demo.
- The adapter can resume the same thread with a structured policy rejection and correction
  request. That rejection-loop behavior has automated coverage; the manual smoke did not execute
  the corrected action set.

Both adapters are untrusted proposers. Deterministic policy remains final authority.
