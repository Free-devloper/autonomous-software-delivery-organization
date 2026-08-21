# Phase 0D Delivery, Telemetry and Platform Evidence

**Status:** Locally implemented and verified for Phase 0D foundation scope  
**Date:** 2026-08-19  
**Scope:** CI-equivalent task surface, telemetry assertions, digest-pinned local images, Compose
infrastructure, Kubernetes/Helm baseline manifests, Argo CD application skeleton and smoke checks.

## Implemented behavior

- API telemetry middleware adds bounded correlation IDs, JSON request logs, OpenTelemetry spans and
  Prometheus metrics at `/metrics`.
- API readiness fails closed unless the configured database can answer a bounded ping and OIDC JWKS
  contains a usable RS256 signing key.
- Local smoke test exercises `/api/v1/health/live` and verifies request metrics are emitted.
- Docker Compose now starts digest-pinned PostgreSQL, OPA and OpenTelemetry Collector services on
  loopback-bound ports with health checks and hardened container settings.
- API and web runtime Dockerfiles use digest-pinned bases and non-root users. `pnpm build` now
  builds TypeScript packages, Next standalone output in a Linux build stage, a `uv.lock`-derived
  hash-checked API requirements file, the API wheel and local images `asdo-api:local` and
  `asdo-web:local`.
- Helm baseline defines API, web and collector workloads, services, config, service accounts,
  probes, resources, HPA, PDB, release-scoped selectors, generated internal service URLs and
  default-deny NetworkPolicy with digest-required image validation.
- Argo CD baseline is present for manual sync only; no cluster write is performed by local
  validation.
- `pnpm deploy:local` and `pnpm test:security` statically validate the platform files and security
  posture expected for this milestone.

## Executed evidence

All commands below were executed locally on 2026-08-19 from
`D:\Office\RoyTechWorkForce\Projects\SoftwareOrg`.

| Command                 | Result                                                                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm build`            | Passed: TypeScript package builds, Linux-stage Next 16.3.1 standalone build, hash-checked API dependency install, API wheel build and Docker image builds for `asdo-api:local` and `asdo-web:local` succeeded |
| `pnpm verify`           | Passed: format, lint, strict TS/Python typecheck, 7 TypeScript tests, 50 Python unit tests at 91.27% coverage, build, image builds and security target                                                        |
| `pnpm test:integration` | Passed: Alembic head `20260818_0002`, upgrade/downgrade/upgrade and real PostgreSQL tenant/audit isolation integration test                                                                                   |
| `pnpm dev-infra`        | Passed: digest-pinned PostgreSQL, OPA and OpenTelemetry Collector containers reached healthy state                                                                                                            |
| `pnpm deploy:local`     | Passed: static platform security validation; intentionally did not apply manifests to a cluster                                                                                                               |
| `pnpm smoke:test`       | Passed: in-process health request and metrics assertion; emitted structured logs with correlation IDs                                                                                                         |
| `pnpm test:security`    | Passed: local secret-pattern check, platform static validation, container HTTP smoke for API/web images and `pnpm audit --prod --audit-level high`                                                            |
| Container smoke         | Passed: `node scripts/container.mjs smoke` started `asdo-api:local` and `asdo-web:local` under UID 10001, read-only root, dropped capabilities and no-new-privileges, then received HTTP 200                  |

## Tooling and environment notes

- GNU Make is not installed in the current Windows PowerShell environment. The Makefile targets
  exist, but evidence was executed with the equivalent `pnpm` commands that the Makefile delegates
  to.
- Docker Desktop is available and was used for Compose health checks and local image builds.
- `helm`, `kind`, `opa`, `cosign`, `syft`, `trivy` and `gitleaks` are not available in `PATH` in
  this environment. Helm rendering, cluster apply, OPA CLI tests, SBOM generation, image signing,
  vulnerability scanning and seeded Gitleaks evidence remain future work.
- The smoke test uses FastAPI's current `TestClient` path and emits a Starlette deprecation warning
  recommending `httpx2`; the warning did not fail the test.

## Remaining limitations

- Remote CI, GitHub branch protection and CodeQL execution are not verified because no external
  write or authenticated provider operation was approved for this milestone.
- Helm manifests are statically validated by repository checks; they were not rendered by Helm or
  applied to kind/EKS in this environment. The API chart requires an explicit secret reference for
  database and OIDC settings before Helm render can succeed.
- OPA is present as local infrastructure and includes an initial default-deny policy, but the API
  still uses the deterministic in-process policy from Phase 0C for authorization.
- OpenBao/Vault integration, WORM audit replication, signed checkpoints, SBOM/signature attestation,
  registry admission policy and production secrets delivery remain planned.
- `/metrics` is local/internal foundation evidence. Production exposure must be restricted by
  ingress, NetworkPolicy and service-monitor design before production deployment claims.
- The chart now includes DNS egress, API-to-collector egress and collector ingress for telemetry.
  Database, OIDC and API-side OPA egress rules still require concrete service identities before live
  deployment.

## Phase boundary recommendation

Phase 0D local foundation work is complete enough to request independent review. Phase 1 should not
start until the user accepts the remaining Phase 0 limitations or provides the missing tooling and
external approvals needed for live cluster, remote CI, SBOM/signing and provider-governance
evidence.
