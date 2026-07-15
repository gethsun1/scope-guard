# Scope Guard contributor guide

Operate only inside this repository. Never inspect or mutate real services, databases,
Docker resources, reverse proxies, SSH state, or other projects. The names RD Social and
EngageFlow refer exclusively to fixtures under `demo/`.

Security decisions must remain deterministic. Model adapters may propose or explain, but
must never override policy. Unknown resources are denied. Never log secrets. Run the
relevant tests after changes and preserve the protected-project integrity invariants.

