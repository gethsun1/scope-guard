# Submission evidence matrix

| Claim | Evidence |
|---|---|
| Deterministic deny-by-default policy | `apps/api/tests/test_policy.py`; 32/32 SentryBench run in `evaluations/sentrybench/results/latest.md` |
| Protected EngageFlow action is blocked | `docs/assets/action-blocked.png`; signature test and 20-event audit described in `docs/LOCAL_END_TO_END_VERIFICATION.md` |
| Approval-gated corrected action | `apps/api/tests/test_signature_flow.py`; boundary and execution screenshots |
| Target-only rollback and protected integrity | `docs/assets/rollback-report.png`; protected SHA-256 `8a8c24fe…e80fdd5` in local verification evidence |
| Real application UI | Six PNG files under `docs/assets/`; Playwright exercises all six routes at desktop and mobile widths |
| Live GPT adapter | Attempted 2026-07-16; quota failure recorded in `docs/LIVE_PROVIDER_VERIFICATION.md` |
| Live Codex adapter | Proposal-only thread and limitations recorded in `docs/LIVE_PROVIDER_VERIFICATION.md` |
| Hosted synthetic demo | `https://scopeguard-vert.vercel.app`; hosted verification script and deployment details in `docs/DEPLOYMENT.md` |
| Release implementation | Commits `c4845b2`, `04c5d1d`, `7669ba8`, and `c3eae1a` |
| Reproducible judge checks | `scripts/verify-clean-clone.sh`; commands in `README.md` |

Screenshot files are 1440×1000 captures of actual application states: overview, inventory,
boundary review, protected-action block, rollback report, and the generated benchmark screen.
