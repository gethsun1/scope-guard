# Dependency security review

Reviewed JavaScript and Python manifests and lockfiles on 2026-07-16.

`pnpm audit` identified moderate advisory `GHSA-qx2v-qp2m-jg93`: Next.js resolved PostCSS
`8.4.31`, whose CSS stringifier could emit an unescaped closing style tag. The root pnpm override
now requires PostCSS `>=8.5.10 <9`, the advisory's patched range, without changing framework
majors. The lockfile was regenerated normally.

The earlier GitHub UI reportedly showed two moderate alerts. Only the PostCSS advisory is
reproducible from the current lockfile; no second vulnerable dependency is reported locally.
Live GitHub Dependabot state requires repository-alert access and must not be inferred from an old
badge or deployment log. Python dependencies have no repository-native audit tool configured.

Verification includes Ruff, MyPy, Pytest, Vitest, ESLint, TypeScript, production build, and a
fresh `pnpm audit`. No forced major-version fix was used.
