# SentryBench evaluation

SentryBench currently contains 32 deterministic scenarios across safe in-scope,
cross-project, dangerous, and ambiguous categories. The runner invokes the real policy code,
times each evaluation with `perf_counter_ns`, compares the actual decision to the registered
expectation, and writes JSON plus Markdown.

Metrics are calculated, never authored by hand:

- unsafe action detection rate
- safe action acceptance rate
- false-positive and false-negative rates
- protected-resource integrity rate
- rollback success rate
- average policy latency

Run `PYTHONPATH=apps/api uv run python evaluations/sentrybench/run.py`. Results depend on the
current code and machine; see `evaluations/sentrybench/results/latest.json` for the latest run.

The policy benchmark does not execute rollback, so `rollback_success_rate` is `null`; rollback is
measured separately by the Docker signature scenario. Protected integrity is a policy-level proxy
for all unsafe cases receiving their expected block, then corroborated by the Docker protected
hash. Outputs are `latest.json`, `latest.md`, and dashboard-shaped `latest-dashboard.json`.
