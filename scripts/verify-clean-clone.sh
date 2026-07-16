#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

missing=()
for command_name in docker uv node pnpm; do
  command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done
if ((${#missing[@]})); then
  printf 'Missing prerequisites: %s\n' "${missing[*]}" >&2
  printf 'Install the versions documented in README.md, then rerun this script.\n' >&2
  exit 1
fi

test -f .env.example || { echo '.env.example is missing' >&2; exit 1; }
test -f uv.lock || { echo 'uv.lock is missing' >&2; exit 1; }
test -f pnpm-lock.yaml || { echo 'pnpm-lock.yaml is missing' >&2; exit 1; }

docker info >/dev/null
docker compose version >/dev/null
uv sync --frozen --all-groups
pnpm install --frozen-lockfile
uv run ruff check .
uv run mypy apps/api
uv run pytest -q
pnpm test
pnpm lint
pnpm typecheck
pnpm build
docker compose config --quiet
docker compose -f demo/docker-compose.demo.yml config --quiet

cat <<'EOF'
Clean-clone checks passed. No containers were started and no volumes or user files were removed.
Next: copy .env.example to .env, keep DEMO_MODE=true, then follow the Docker demo instructions in README.md.
EOF
