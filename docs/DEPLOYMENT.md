# Deployment

## Frontend / Vercel

Deploy `apps/web`, set `NEXT_PUBLIC_API_URL` to the HTTPS API origin, and preserve the
standalone Next.js output. Replace the local demo token flow before exposing mutations.

## Backend / Railway

Build with `apps/api/Dockerfile`; health path is `/health`; start command is the image default.
Set `ALLOWED_ORIGINS`, `DEMO_MODE`, provider credentials, a strong audit secret, and database
URL. SQLite on an ephemeral or multi-replica service can lose/corrupt state: use PostgreSQL and
durable audit storage for production.

## Writable demo

Use `demo/docker-compose.demo.yml` only on a disposable Docker host. It does not require
privileged mode. Never add the Docker socket, host root, production SSH material, or production
credentials. A hosted dashboard may be read-only if container execution is unavailable.

