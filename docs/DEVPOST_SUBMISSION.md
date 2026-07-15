# Devpost submission draft

## Project name

Scope Guard (Codex Sentry)

## Elevator pitch

An intent-bound control plane that lets Codex move quickly while deterministic policy keeps
files, services, databases, networks, and neighboring projects inside an approved boundary.

## Category

Developer Tools — OpenAI Build Week Challenge.

## Inspiration

Powerful coding agents increasingly deploy software. Shared environments add a new failure
mode: completing the right task while modifying the wrong project.

## What it does

GPT-5.6 proposes a typed boundary; a person approves it; Codex proposes actions; deterministic
policy blocks scope drift; an isolated Docker runner executes approved operations; validation,
rollback, audit, and SentryBench provide evidence.

## How it was built

Next.js, TypeScript, FastAPI, Pydantic, Docker Compose, OpenAI Responses API adapter, Codex
adapter, SSE, SHA-256 audit chaining, Pytest, Vitest, and a 32-scenario benchmark.

## Challenges

Maintaining non-root ownership during Docker named-volume initialization, keeping the runner
offline while publishing the API, and preventing substring resource collisions during parsing.

## Accomplishments and lessons

The real container demo blocks EngageFlow before execution, returns a correction, approval-
gates RD Social, deliberately fails health, restores the target hash, preserves the protected
hash, and produces verified audit evidence. The key lesson: models are excellent proposers and
collaborators, but authorization should be deterministic and inspectable.

## GPT-5.6 and Codex

GPT-5.6 has a strict Responses API planner role: interpretation, resources, risk, validation,
rollback—never enforcement. Codex accelerated the build and is represented in-product by a
typed live integration point and deterministic demo provider with the same rejection loop.

## Testing / repository / hosted demo

Follow the root README. Add repository URL, hosted read-only dashboard URL, video URL, and
screenshots before submission. Run `/feedback` in the primary Codex session and paste the real
returned session ID here; do not invent it.

## What comes next

PostgreSQL persistence, signed audit export, OAuth/SSO, inventory adapters, policy packs, and
production-grade live Codex transport.

