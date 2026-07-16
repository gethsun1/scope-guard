.PHONY: setup dev demo-up demo-down demo-reset test lint typecheck e2e eval build verify smoke-gpt smoke-codex
setup:
	uv sync --all-groups
	pnpm install
dev:
	docker compose up --build
demo-up:
	COMPOSE_PARALLEL_LIMIT=2 docker compose -f demo/docker-compose.demo.yml up --build -d
demo-down:
	docker compose -f demo/docker-compose.demo.yml down
demo-reset:
	docker compose -f demo/docker-compose.demo.yml down -v --remove-orphans
	COMPOSE_PARALLEL_LIMIT=2 docker compose -f demo/docker-compose.demo.yml up --build -d --wait
test:
	uv run pytest
	pnpm test
lint:
	uv run ruff check .
	pnpm lint
typecheck:
	uv run mypy apps/api
	pnpm typecheck
e2e:
	uv run pytest apps/api/tests/test_signature_flow.py
eval:
	PYTHONPATH=apps/api uv run python evaluations/sentrybench/run.py
build:
	pnpm build
	docker compose build
verify: lint typecheck test eval build
	docker compose config --quiet
	docker compose -f demo/docker-compose.demo.yml config --quiet
smoke-gpt:
	PYTHONPATH=apps/api DEMO_MODE=false uv run python -m scope_guard.smoke gpt
smoke-codex:
	PYTHONPATH=apps/api CODEX_PROVIDER=live uv run python -m scope_guard.smoke codex
