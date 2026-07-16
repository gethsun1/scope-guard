# Scope Guard

> **Let coding agents move fast—without letting them wander.**

Scope Guard, internally codenamed **Codex Sentry**, is an intent-bound execution control
plane for coding agents. It lets a model interpret a task and propose a plan, but places a
deterministic policy engine between every proposed action and an isolated runner.

Live demo: [scopeguard-vert.vercel.app](https://scopeguard-vert.vercel.app). Its API uses a
synthetic in-memory state machine with no shell or Docker access. The complete writable sandbox
remains intentionally local and Docker-based.

![Scope Guard dashboard](docs/assets/dashboard.png)

## The problem

Shared development environments make scope drift dangerous: an agent can successfully
deploy the requested service while also restarting a neighbor, reading an unrelated secret,
or migrating the wrong database. A normal sandbox answers what is technically reachable.
Scope Guard also asks whether the action belongs to the approved task and project.

## Thirty-second explanation

1. GPT-5.6 interprets natural-language intent and proposes a typed boundary.
2. A person approves the target, protected resources, validation, and rollback plan.
3. Codex proposes actions. A deterministic engine parses and evaluates every action.
4. Allowed actions run through a predefined-operation Docker runner; protected actions stop.
5. Target health, protected integrity, rollback, and a hash-chained audit report provide proof.

## Signature scenario

> Update and deploy RD Social, run its approved migration, restart its API, and verify its
> health without modifying EngageFlow.

The deterministic demo Codex adapter first edits RD Social, then mistakenly proposes
`systemctl restart engageflow-api`. Scope Guard returns `BLOCK_PROTECTED_RESOURCE` and a
structured correction. The corrected RD Social restart requires approval. Failure injection
then makes RD Social unhealthy, triggers target-only rollback, and proves EngageFlow retained
the same hash and health state.

## Features

- Typed project inventory and resource graph
- GPT-5.6 Responses API adapter plus clearly labeled offline demo planner
- Read-only Codex app-server proposal adapter plus deterministic `codex_demo` event provider
- Structured command parsing, normalized paths, and deterministic deny-by-default policy
- Explicit boundary and medium/high-risk action approvals
- Non-root Docker runner with no socket, host-root, privileges, secrets, or external network
- Snapshots, target validation, protected-resource verification, and task-scoped rollback
- SSE audit timeline and downloadable JSON/Markdown execution reports
- 32-scenario SentryBench with generated metrics
- Responsive DevOps control-plane interface—not a chat wrapper

## Architecture

```mermaid
flowchart LR
  U[Developer] --> W[Next.js control plane]
  W --> A[FastAPI orchestrator]
  A --> P[GPT-5.6 planner]
  A --> C[Codex adapter]
  C --> E[Deterministic policy engine]
  E -->|allow / approval| R[Predefined Docker runner]
  E -->|block + context| C
  R --> RD[RD Social target]
  R -. integrity only .-> EF[EngageFlow protected]
  A --> AU[Hash-chained audit]
```

Details: [architecture](docs/ARCHITECTURE.md) and [threat model](docs/THREAT_MODEL.md).

### Responsibility split

**GPT-5.6** interprets intent, proposes resources, explains risk, and drafts validation and
rollback plans. Its strict JSON is validated and never grants authority.

**Codex** accelerated development and can collaborate through proposed actions, receive
structured policy rejection, and continue in the same thread. `codex_demo` is deterministic;
the proposal-only `codex_live` smoke path was exercised locally, but it is not the default.

**The policy engine** is final authority. It parses commands, extracts resources, detects
danger, matches the approved manifest, denies unknowns, and produces deterministic decisions.

## Security model

Unknown resources are denied. Model output cannot expand a manifest. Mutations are approval
gated and snapshotted. The runner exposes only named demo operations, runs as UID 10001 with
all Linux capabilities dropped, a read-only root, CPU/memory limits, and an internal Docker
network. Neither `/`, SSH material, nor `/var/run/docker.sock` is mounted.

## Requirements

- Supported development systems: Linux and WSL2. macOS may work with Docker Desktop but is not
  part of the verified matrix; Windows should use WSL2.
- Docker Desktop/Engine with Compose v2+
- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and pnpm 11+
- GNU Make (optional wrapper; direct commands below work without it)

## Setup

```bash
cp .env.example .env
uv sync --all-groups
pnpm install
```

No paid credential is needed with `DEMO_MODE=true`.

## Run locally

```bash
# Complete isolated signature environment
docker compose -f demo/docker-compose.demo.yml up --build -d --wait

# Frontend (separate terminal)
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm --filter web dev
```

Open `http://localhost:3000`. The API OpenAPI UI is at `http://localhost:8000/docs`.
State-changing API examples use `X-Demo-Token: scope-guard-demo`; this is explicitly local
demo authentication and must be changed or replaced for a hosted environment.

## Demo

1. Open **Guarded task** and interpret the seeded instruction.
2. Review and approve the GPT-5.6 demo manifest.
3. Open **Execution**, start execution, and inspect the blocked EngageFlow action.
4. Approve the corrected RD Social restart.
5. Observe failed target health, rollback, protected integrity, and download the report.

Reset everything deterministically:

```bash
docker compose -f demo/docker-compose.demo.yml down -v --remove-orphans
docker compose -f demo/docker-compose.demo.yml up --build -d --wait
```

See the [under-three-minute script](docs/DEMO_SCRIPT.md).

## Environment variables

`.env.example` documents all settings. Live planning requires `DEMO_MODE=false`, an
`OPENAI_API_KEY`, and a supported `OPENAI_MODEL`. Live Codex requires the `codex` CLI with
app-server support and existing authentication. Never place secrets in prompts, logs, or
committed files. Manual smoke commands are `make smoke-gpt` and `make smoke-codex` (or their
documented underlying commands); neither runs in CI.

## SentryBench

```bash
PYTHONPATH=apps/api uv run python evaluations/sentrybench/run.py
```

This writes actual results to `evaluations/sentrybench/results/latest.json` and `.md`. The
committed latest run contains 32/32 expected decisions; rerun it on your machine rather than
treating old results as immutable claims.

## Test and build

```bash
uv run ruff check .
uv run mypy apps/api
uv run pytest -q
pnpm test
pnpm lint
pnpm typecheck
pnpm build
docker compose -f demo/docker-compose.demo.yml config --quiet
```

For a fresh-clone, non-destructive prerequisite/install/test pass, run
`./scripts/verify-clean-clone.sh`. It never installs system packages, starts containers, removes
volumes, or reads secrets. To verify the hosted synthetic workflow, set `FRONTEND_URL`, `API_URL`,
and `DEMO_API_TOKEN`, then run `./scripts/verify-hosted-demo.sh`; the token is never printed.

Download a task report from the Execution screen, or request
`GET /api/tasks/{task_id}/report?format=json` (use `format=md` for Markdown).

With GNU Make installed: `make test`, `make lint`, `make typecheck`, `make e2e`, `make eval`,
`make build`, or `make verify`.

On Ubuntu, install the optional wrapper with `sudo apt-get update && sudo apt-get install -y make`.

## Deployment

The Next.js app is Vercel-compatible. The FastAPI image and `railway.json` are
Railway-compatible. SQLite is for a single-instance demo only; production should use
PostgreSQL and durable audit storage. The writable Docker scenario belongs on an isolated,
unprivileged container host. See [deployment guidance](docs/DEPLOYMENT.md).

## Current limitations

- Inventory is registered synthetic data, not host discovery.
- Task state is process-local; SQLite/PostgreSQL persistence is the next production step.
- Live providers are opt-in; the GPT-5.6 request reached OpenAI but did not pass because the
  account returned `insufficient_quota`. See `docs/LIVE_PROVIDER_VERIFICATION.md`.
- Shell analysis intentionally supports a constrained subset; execution is predefined only.
- Local demo authentication is not enterprise identity.

## Roadmap

Durable PostgreSQL state, signed audit export, OAuth/SSO, organization policy packs,
repository-aware inventory adapters, richer shell AST support, and deployment-provider
integrations—without granting a model final policy authority.

## Hackathon disclosure

Built for the OpenAI Build Week Developer Tools category. Codex accelerated implementation,
review, debugging, tests, container verification, and documentation. GPT-5.6 is integrated as
the live structured planner adapter; the credential-free demo uses the same schema and clearly
labels deterministic output. See [Codex collaboration history](docs/CODEX_COLLABORATION.md).

## License

[MIT](LICENSE)
