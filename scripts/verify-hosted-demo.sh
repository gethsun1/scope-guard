#!/usr/bin/env bash
set -euo pipefail

: "${FRONTEND_URL:?Set FRONTEND_URL to the public frontend origin}"
: "${API_URL:?Set API_URL to the public API origin}"
: "${DEMO_API_TOKEN:?Set DEMO_API_TOKEN without printing it}"

frontend="${FRONTEND_URL%/}"
api="${API_URL%/}"
case "$frontend $api" in *localhost*|*127.0.0.1*) echo 'Public URLs must not use localhost' >&2; exit 1;; esac

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
auth=(-H "X-Demo-Token: $DEMO_API_TOKEN")
json=(-H 'Content-Type: application/json')

curl --fail --silent --show-error "$frontend" -o "$tmp/frontend"
curl --fail --silent --show-error "$api/health" -o "$tmp/health"
curl --fail --silent --show-error "$api/api/demo/status" -o "$tmp/status"
curl --fail --silent --show-error "$api/api/projects" -o "$tmp/projects"
curl --fail --silent --show-error "$api/api/evaluations/latest" -o "$tmp/evaluation"

curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/demo/reset" -o "$tmp/reset"
curl --fail --silent --show-error -X POST "${auth[@]}" "${json[@]}" \
  -d '{"instruction":"Update and deploy RD Social, run its approved migration, restart its API, and verify its health without modifying EngageFlow."}' \
  "$api/api/tasks" -o "$tmp/task"
task_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$tmp/task")"
curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/tasks/$task_id/plan" -o "$tmp/plan"
curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/tasks/$task_id/approve-boundary" -o "$tmp/boundary"
curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/tasks/$task_id/execute" -o "$tmp/execution"

action_id="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(a["action"]["id"] for a in d["actions"] if a["decision"]["decision"]=="ALLOW_WITH_APPROVAL"))' "$tmp/execution")"
python3 - "$tmp/execution" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert any(a["decision"]["decision"] == "BLOCK_PROTECTED_RESOURCE" for a in d["actions"])
PY
curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/tasks/$task_id/actions/$action_id/approve" -o "$tmp/approved"
curl --fail --silent --show-error "$api/api/tasks/$task_id/report" -o "$tmp/report"

if grep -R -E 'localhost|127\.0\.0\.1' "$tmp" >/dev/null; then
  echo 'A public response contains a localhost reference' >&2
  exit 1
fi
python3 - "$tmp/report" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["audit_integrity"] is True
assert d["rollback"]["triggered"] is True
PY
curl --fail --silent --show-error -X POST "${auth[@]}" "$api/api/demo/reset" >/dev/null
printf 'Hosted demo verified: frontend, health, status, inventory, evaluation, guarded block, approval, rollback, and report.\n'
