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

