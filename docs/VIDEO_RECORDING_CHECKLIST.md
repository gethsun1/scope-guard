# Video recording checklist

Target runtime: **2:45**, hard stop at 2:50.

## Before recording

- Local URLs: `http://localhost:3000`, API health `http://localhost:8000/health`.
- Hosted URL: `https://scopeguard-vert.vercel.app`.
- Use `DEMO_MODE=true`, `CODEX_PROVIDER=demo`, the isolated Docker Compose environment, and no
  production credentials or infrastructure.
- Reset with `docker compose -f demo/docker-compose.demo.yml down -v --remove-orphans`, then
  start with `docker compose -f demo/docker-compose.demo.yml up --build -d --wait`.
- Confirm both synthetic apps are healthy and clear browser local storage.

## Click and narration sequence

1. **0:00–0:20 — Overview.** Explain that a normal sandbox limits reachability; Scope Guard
   additionally enforces the resources authorized by this task.
2. **0:20–0:50 — Inventory and guarded task.** Scan inventory. Identify RD Social as target and
   EngageFlow as protected. Submit the instruction. Explain that GPT-5.6 interprets intent and
   proposes strict structured data; demo mode is visibly deterministic. Approve the manifest.
3. **0:50–1:30 — Execution.** Start execution. Explain that Codex proposes actions but the
   deterministic engine is final authority. Pause on `systemctl restart engageflow-api` and
   `BLOCK_PROTECTED_RESOURCE`; show the rejection and corrected RD Social action.
4. **1:30–1:55 — Approval and failure.** Approve the target restart. Point out the deliberate
   RD Social health failure and automatic target-only rollback.
5. **1:55–2:20 — Report.** Show recovered RD Social, unchanged EngageFlow, valid audit chain,
   and download the report.
6. **2:20–2:40 — SentryBench.** Show the freshly generated scenario count and measured metrics;
   state that it is a synthetic deterministic benchmark, not a general security guarantee.
7. **2:40–2:45 — Close.** “Let agents move fast—without letting them wander.”

Expected evidence: one protected block, same-workflow correction, one human approval, one target
failure, successful RD Social rollback, and unchanged EngageFlow hash and health.

Say the labels exactly: “GPT-5.6 · DEMO” interprets the boundary, “Codex · DEMO” proposes the
signature actions, deterministic policy blocks or approval-gates them, and the Docker runner alone
mutates the synthetic target. The deliberate failure is RD Social health; the expected corrected
action is the `rdsocial-api` restart; rollback restores RD Social while EngageFlow stays unchanged.

## Backup plan

Record a clean local take after reset. If the hosted dashboard is unavailable, use the verified
local Docker environment. Keep a second take of the block/rollback sequence and a locally saved
report. Never replace the Docker runner with host execution for the recording.
