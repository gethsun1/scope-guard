# Deployment

The recommended public split is **Next.js on Vercel → FastAPI on Railway → deterministic
demo provider or a separately isolated runner**. A public deployment must never connect to a
production VPS, mount a Docker socket, load SSH keys, expose arbitrary shell execution, or
contain production credentials.

## Confirmed public architecture

The production frontend is Vercel project `gethsun1s-projects/scopeguard`; the production API is
Railway project `scopeguard`, service `scopeguard-api`. The browser uses the exact HTTPS Railway
origin through `NEXT_PUBLIC_API_URL`; Railway CORS permits only the Vercel production origin.
Public provider labels explicitly identify deterministic demo mode.

## Vercel

The deployed app-scoped configuration is `apps/web/vercel.json`: context `apps/web`, `npm install`,
`npm run build`, and framework-managed Next.js output. `NEXT_PUBLIC_API_URL` is set at build and
runtime to `https://scopeguard-api-production.up.railway.app`; it is public configuration.

```bash
vercel link --cwd apps/web --project scopeguard --scope gethsun1s-projects
vercel env add NEXT_PUBLIC_API_URL production --cwd apps/web
vercel deploy --cwd apps/web --yes --scope gethsun1s-projects -A apps/web/vercel.json --archive=tgz
vercel deploy --cwd apps/web --prod --yes --scope gethsun1s-projects -A apps/web/vercel.json --archive=tgz
vercel inspect DEPLOYMENT_URL --logs
# Roll back by promoting a known-good deployment in the dashboard or CLI.
```

The current fixed demo mutation token is intentionally low assurance. Use the public demo only
with synthetic, resettable data and rate limiting, or replace it with real identity before any
non-demo use.

## Railway control plane

Repository-root `railway.json` builds `apps/api/Dockerfile`; the image starts Uvicorn on
`0.0.0.0:${PORT:-8000}` and Railway checks `/health`.

```bash
railway link                 # select scopeguard
railway service              # select scopeguard-api
railway variables --set APP_ENV=production --set DEMO_MODE=true --set CODEX_PROVIDER=demo
# Set secret values by name without echoing them: DEMO_API_TOKEN, AUDIT_SIGNING_SECRET.
railway up --service scopeguard-api
railway logs --service scopeguard-api
curl --fail https://scopeguard-api-production.up.railway.app/health
# Roll back by redeploying the last known-good Railway deployment.
```

Set `APP_ENV=production`, `DEMO_MODE=true`, `CODEX_PROVIDER=demo`, `DEMO_RUNNER_URL=inmemory://`, `ALLOWED_ORIGINS` to the exact
Vercel origin, `DEMO_API_TOKEN` to a deployment secret, and `AUDIT_SIGNING_SECRET` to a distinct
secret. Do not set live provider credentials on the public demo unless the runner architecture
has been separately reviewed. `ALLOWED_ORIGINS` accepts a comma-separated list.

## State and runner

Task/audit state is process-local; restarts and
multiple replicas lose or diverge state. Run one replica and describe it as an ephemeral demo.
`POST /api/demo/reset` restores registered synthetic state. Report downloads work only while the originating
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
