# Deployment

The recommended public split is **Next.js on Vercel → FastAPI on Railway → deterministic
demo provider or a separately isolated runner**. A public deployment must never connect to a
production VPS, mount a Docker socket, load SSH keys, expose arbitrary shell execution, or
contain production credentials.

## Vercel dashboard

`vercel.json` builds the `web` workspace. Set `NEXT_PUBLIC_API_URL` to the Railway HTTPS origin
before building; it is a public browser value, not a secret. From an authenticated developer
terminal:

```bash
vercel --prod
```

The current fixed demo mutation token is intentionally low assurance. Use the public demo only
with synthetic, resettable data and rate limiting, or replace it with real identity before any
non-demo use.

## Railway control plane

`railway.json` builds `apps/api/Dockerfile`; the image starts
`uvicorn scope_guard.main:app --host 0.0.0.0 --port 8000` and Railway checks `/health`.

```bash
railway up
railway domain
```

Set `APP_ENV=production`, `DEMO_MODE=true`, `CODEX_PROVIDER=demo`, `ALLOWED_ORIGINS` to the exact
Vercel origin, `DEMO_API_TOKEN` to a deployment secret, and `AUDIT_SIGNING_SECRET` to a distinct
secret. Do not set live provider credentials on the public demo unless the runner architecture
has been separately reviewed. `ALLOWED_ORIGINS` accepts a comma-separated list.

## State and runner

Task/audit state is currently process-local despite the documented `DATABASE_URL`; restarts and
multiple replicas lose or diverge state. Run one replica and describe it as an ephemeral demo.
Reset restores registered synthetic state. Report downloads work only while the originating
process retains the task.

Railway should either use a deterministic no-shell provider or call a separately isolated runner
that exposes the existing named operation allowlist. Never mount `/var/run/docker.sock`, host
root, SSH material, or production secrets. The local `demo/docker-compose.demo.yml` is the only
currently verified writable topology; it is not a production deployment template.

## Verification and limitations

The hosted demo is deployed at `https://scopeguard-vert.vercel.app`; its Railway API is
`https://scopeguard-api-production.up.railway.app`. Health, exact-origin CORS, reset, the complete
synthetic block/approval/rollback workflow, audit integrity, and frontend reachability were
verified after deployment. Durable PostgreSQL audit storage, production identity, rate limiting,
and multi-replica coordination remain future work.
