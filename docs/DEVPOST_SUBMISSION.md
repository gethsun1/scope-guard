# Devpost submission draft

## Project name

Scope Guard (Codex Sentry)

## Elevator pitch

An intent-bound execution control plane that lets coding agents move quickly while deterministic
policy keeps files, services, databases, networks, and neighboring projects inside an approved
task boundary.

## Category

Developer Tools — OpenAI Build Week Challenge.

## Inspiration

Agents can complete the requested deployment while accidentally touching a neighboring project.
A conventional sandbox controls reachability; Scope Guard also controls task authorization.

## What it does

It inventories synthetic projects, interprets intent, presents an approval boundary, intercepts
every proposed action, blocks protected or unknown resources, approval-gates target mutations,
validates health, performs target-only rollback, and exports hash-chained audit evidence.

## How it was built

Next.js, TypeScript, FastAPI, Pydantic, the OpenAI Responses API, Codex app-server JSONL protocol,
Docker Compose, SHA-256 audit chaining, Pytest, Vitest, Playwright, and SentryBench.

## How GPT-5.6 was used

The optional `gpt_live` planner uses strict structured output for intent, resource boundaries,
risk, validation, rollback, and confidence. Pydantic validates every result and ambiguity fails
closed. The credential-free submission demo uses visibly labeled `gpt_demo`. The live GPT smoke
was attempted with a developer-supplied local credential, but OpenAI returned `insufficient_quota`;
no live structured plan was produced. The credential was never committed or deployed.

## How Codex was used

Codex accelerated implementation, review, testing, debugging, and documentation. The product's
`codex_live` adapter starts/resumes an app-server thread in read-only proposal mode, validates
typed actions, returns deterministic rejection context to the same thread, and records its ID.
A manual live proposal smoke succeeded; `codex_demo` remains the reproducible signature provider.

## Challenges encountered

Keeping Docker volumes non-root, separating protected-resource names without substring mistakes,
preserving a same-thread rejection loop, satisfying strict schemas, and keeping WSL stable while
Docker, Next.js, and browser tooling shared limited memory.

## Accomplishments

The real Docker scenario blocked EngageFlow before execution, returned a correction, required
approval for RD Social, injected a health failure, restored the target, preserved the protected
hash, and verified a 20-event audit chain. All 32 current SentryBench decisions pass.

## What was learned

Models are strong interpreters and proposers; authorization is safer when deterministic,
inspectable, approval-aware, and independent of model confidence.

## What comes next

Durable PostgreSQL events, production identity, signed exports, policy packs, inventory adapters,
and separately isolated hosted runners.

## Repository, testing, installation, and platforms

Repository: `https://github.com/gethsun1/scope-guard`. Follow the root README or run
`./scripts/verify-clean-clone.sh`. Supported development platforms are
Linux and WSL2 with Docker Compose v2, Python 3.11+, uv, Node 20+, and pnpm 11. Run Ruff, MyPy,
Pytest, Vitest, ESLint, TypeScript, Next.js build, Compose validation, and SentryBench using the
documented commands. The script checks prerequisites, installs only project dependencies, and
runs non-destructive validation. GNU Make is optional. The signature demo itself requires Docker
Compose and uses only the synthetic RD Social and EngageFlow fixtures.

## Hosted demo and video

Live demo: `https://scopeguard-vert.vercel.app`. Video: `YOUTUBE_DEMO_URL`. The public configuration must remain
synthetic, resettable, and disconnected from production infrastructure.

Codex feedback session: `CODEX_FEEDBACK_SESSION_ID`.
