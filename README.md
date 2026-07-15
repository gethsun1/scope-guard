# Scope Guard

> Let coding agents move fast—without letting them wander.

Scope Guard (Codex Sentry) is an intent-bound execution control plane for coding agents.
It turns a task into an approved resource boundary, checks every proposed action with a
deterministic policy engine, executes allowed operations in a synthetic sandbox, verifies
protected resources, and records a tamper-evident audit trail.

The signature demo safely deploys synthetic RD Social while synthetic EngageFlow remains
protected. Full setup, architecture, evaluation, and deployment instructions are added as
the implementation milestones land.

## Safety

This repository never connects to real RD Social, EngageFlow, production databases, or
production infrastructure. Both named applications are disposable local fixtures.

## Status

Active implementation for the OpenAI Build Week Developer Tools category.

License: MIT.

