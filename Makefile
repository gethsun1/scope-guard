.PHONY: setup dev demo-up demo-down demo-reset test lint typecheck e2e eval build verify
setup:
	uv sync --all-groups
	pnpm install
dev:
	docker compose up --build
demo-up:
	docker compose -f demo/docker-compose.demo.yml up --build -d
demo-down:
	docker compose -f demo/docker-compose.demo.yml down
demo-reset:
	docker compose -f demo/docker-compose.demo.yml down -v --remove-orphans
	docker compose -f demo/docker-compose.demo.yml up --build -d --wait
test:
	uv run pytest
	pnpm test
lint:
	uv run ruff check .
	pnpm lint
typecheck:
	uv run mypy
	pnpm typecheck
e2e:
	uv run pytest apps/api/tests/test_signature_flow.py
eval:
	uv run python evaluations/sentrybench/run.py
build:
	pnpm build
	docker compose build
verify: lint typecheck test eval build
	docker compose -f demo/docker-compose.demo.yml config --quiet

