# Final gap analysis

Audited against commit `52f1447` on 2026-07-16. This is an implementation audit, not a
claim of production readiness.

## Product

The six product views are represented by Overview (`/`), Inventory (`/inventory`), New
guarded task (`/tasks/new`), Live execution (`/execution`), the execution report embedded in
the execution view, and SentryBench (`/sentrybench`). There is no independently addressable
report route yet. Navigation and the signature workflow are connected to the API, and error,
empty, busy, blocked, approval, completed, and rollback presentations exist.

Two material gaps remain. **Scan inventory** is a placeholder button, and the task instruction
is read-only. The interface also hard-codes `codex_demo` and `GPT-5.6 · DEMO` instead of showing
the providers returned by the control plane. Overview shows protected integrity as 100% before
there is an execution result; that must become an explicit not-yet-measured state. Browser and
mobile verification has not been automated, and the required real screenshots do not exist.

## Backend and evidence

Health, inventory, task creation, planning, boundary approval, guarded execution, action
approval/rejection, rollback, SSE events, report download, benchmark results, demo reset, and
demo status endpoints exist. The deterministic signature path snapshots the two synthetic
projects, blocks the protected service, approval-gates the target restart, injects a target
health failure, restores only RD Social, verifies EngageFlow, and builds a hash-chain-backed
report.

The event endpoint replays the events already held by the task and closes; it does not stream
new events while an execution is progressing. Tasks, events, snapshots, and reports are held in
process memory, so reports are generated from real audit events but not durable persisted
events. The configured database dependency is not currently used. Reset delegates to the
isolated runner and clears in-process tasks, making the local synthetic reset deterministic;
multi-replica or restart-safe behavior is not implemented.

## GPT-5.6 planner

The live planner uses the official asynchronous OpenAI SDK, the Responses API, a configurable
`OPENAI_MODEL` (default `gpt-5.6`), strict JSON Schema output, and Pydantic validation. Demo mode
remains deterministic and the API key is read from configuration/environment only. Boundary
audit events record the prompt version.

It is not complete for this phase. The planner schema omits approval-required resources,
provider type is not represented in the planner result, and semantic ambiguity is not rejected.
There are no bounded retries or explicit request timeout, no mocked live-provider tests, and no
manual smoke command. The existing validation handles malformed JSON/schema output, but missing
or ambiguous plan semantics need explicit fail-closed checks. No credentialed live smoke run has
been recorded.

## Codex integration

`DemoCodexAdapter` supplies a deterministic sequence of typed proposed actions. The engine
intercepts each one with the policy engine, returns structured rejection data into the audit
workflow, and then considers a corrected target action. `CodexAppServerAdapter` is only a stub
that raises an availability error. The execution engine always instantiates the demo adapter.

The installed Codex CLI exposes the experimental JSONL-over-stdio app-server protocol, including
initialize, thread start/resume, turn start, and streamed item/turn events. Scope Guard does not
yet use it: there is no thread persistence, proposed-action extraction, same-thread rejection
feedback, event mapping, live-provider selection, graceful availability fallback, or manual smoke
command. Live Codex integration has therefore not been demonstrated.

## Deployment

The web app has Vercel configuration and a production-configurable `NEXT_PUBLIC_API_URL`. The API
has a Railway Dockerfile configuration, `/health`, configurable CORS, and provider/environment
settings. The demo Compose runner is isolated and does not mount a Docker socket or host SSH
material.

The current mutation token is a public fixed demo value, in-memory state is unsuitable for
multi-replica or durable hosting, and the Railway configuration does not explicitly document a
start command. A hosted-safe mode must use only the deterministic provider (or a separately
isolated runner), expose no general shell capability, document ephemeral state/reset behavior,
and clearly label its limitations. No Vercel or Railway deployment has been performed or
verified in this phase.

## Work required for submission

1. Record the pre-change local and Docker signature verification from actual commands.
2. Finish both live adapters with fail-closed tests and manual, non-CI smoke commands.
3. Connect every UI control, derive provider/metrics from real state, add the report route, and
   verify all routes at desktop and mobile widths with Playwright screenshots.
4. Make hosted-demo constraints and environment configuration explicit.
5. Re-run SentryBench and the complete verification suite, then refine submission and recording
   documentation without overstating unexecuted live or hosted checks.
