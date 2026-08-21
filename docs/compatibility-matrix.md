# Compatibility Matrix

**Status:** Phase 0A through Phase 0D local foundation selections locked and verified where noted  
**Date:** 2026-08-19

## Selection policy

Phase 0 build approval was received. Select releases immediately before their owning milestone from
official release channels, lock application dependencies in `pnpm-lock.yaml` and `uv.lock`, and pin
container images by digest. A version is recorded as verified only after its applicable repository
commands execute successfully; later-milestone selections remain `TBD`. Do not use unreleased
versions or mutable production tags.

Before acceptance, capture runtime version, package/image version, upstream support status,
architecture support, license, CVE/scanner result, compatibility evidence, digest/checksum and
upgrade owner. Generate CycloneDX or SPDX SBOMs with Syft and sign/attest released images with
Cosign.

## Application and orchestration baseline

| Capability             | Required candidate                                   | Version/digest state                    | Compatibility constraint and Phase 0 evidence                                                                                    |
| ---------------------- | ---------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| JavaScript runtime     | Node.js maintained LTS                               | 24.18.0                                 | Pinned by runtime files; observed `v24.18.0`; full Phase 0A verification passed                                                  |
| JS package manager     | pnpm                                                 | 11.22.0                                 | Pinned by `packageManager`; frozen lock install and Phase 0A verification passed                                                 |
| Web framework          | Next.js                                              | 16.3.1                                  | Locked with React 19.2.8; production build passed                                                                                |
| UI runtime             | React / React DOM                                    | 19.2.8 / 19.2.8                         | Exact matching pair in web and UI peer contract; build/unit suite passed                                                         |
| Language               | TypeScript strict                                    | 6.0.3                                   | Strict workspace typecheck and build passed                                                                                      |
| UI/editor/data         | Tailwind CSS; Monaco; TanStack Query                 | 4.3.3; TBD; TBD                         | Tailwind Phase 0A build passed; editor/data dependencies belong to later milestones                                              |
| Frontend tests         | Vitest, React Testing Library, Playwright            | 4.1.10; 16.3.2; TBD                     | Phase 0A component tests passed; browser matrix remains a later milestone                                                        |
| Python runtime         | Maintained CPython                                   | 3.13.13                                 | Pinned by runtime files; observed 3.13.13; Python verification passed                                                            |
| Python package manager | uv                                                   | 0.11.7                                  | Observed 0.11.7; committed `uv.lock`; frozen workspace sync passed                                                               |
| API stack              | FastAPI, Pydantic, SQLAlchemy, Alembic, asyncpg      | 0.141.1; 2.13.4; 2.0.52; 1.19.1; 0.31.0 | PyPI releases and present `uv.lock` verified; typecheck, unit, build, migration round trip and PostgreSQL RLS integration passed |
| API auth/client crypto | PyJWT, cryptography, httpx                           | 2.13.0; 50.0.0; 0.28.1                  | Locked in `uv.lock`; RS256/JWKS token tests, OIDC config validation and full Phase 0C verification passed                        |
| API telemetry          | OpenTelemetry Python SDK/exporter; Prometheus client | 1.44.0; 1.44.0; 0.26.0                  | Locked in `uv.lock`; telemetry unit tests, smoke metrics assertion and full Phase 0D verification passed                         |
| Durable workflow       | Temporal Server and Python SDK                       | TBD                                     | Server/SDK support matrix, deterministic replay and upgrade test                                                                 |
| Agent graph            | LangGraph                                            | TBD                                     | Python/model-gateway compatibility; checkpoint and interrupt/replay tests                                                        |
| Contracts              | Zod, JSON Schema and OpenAPI 3.1                     | Zod 4.4.3; framework-generated OpenAPI  | Versioned health contract and schema parity tests passed; generation/diff tooling remains later                                  |

## Data, platform and observability baseline

| Capability            | Required candidate                                         | Version/digest state                                                                                                                 | Compatibility constraint and evidence                                                                                                                                                               |
| --------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Transaction/vector DB | PostgreSQL + pgvector                                      | PostgreSQL 18.4 image pinned; pgvector TBD                                                                                           | Official image `postgres:18.4@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636` validated on amd64/arm64; initial relational migration/RLS suite passed; pgvector remains 1D |
| Cache                 | Valkey or compatible Redis protocol                        | TBD                                                                                                                                  | Client/protocol/TLS/ACL compatibility and failure semantics tested                                                                                                                                  |
| Object storage        | S3-compatible implementation                               | TBD                                                                                                                                  | Conditional write, multipart, checksum, retention and encryption contracts                                                                                                                          |
| Identity              | Keycloak-compatible OIDC provider                          | TBD                                                                                                                                  | Discovery/JWKS/rotation/logout/claim/fresh-auth tests                                                                                                                                               |
| Secrets               | OpenBao or Vault-compatible interface                      | OpenBao 2.6.1 selected/deferred; image digest `sha256:5b2486ab0fb90bbc788cc345b0a08616dfb375873ee8be5df3a2fd4d378a67e0`              | Version selected for later milestone; auth method, lease/renew/revoke and audit behavior remain contract-test requirements                                                                          |
| Policy                | OPA                                                        | 1.19.1 image digest `sha256:378b7db7218985444b7bc14f0b0f5b05c864b9481fe470e133654a7fc084072c`                                        | Compose service and initial policy file passed Phase 0D health/static validation; API-side OPA integration remains later                                                                            |
| Kubernetes            | Amazon EKS reference; kind local                           | TBD                                                                                                                                  | Validate supported EKS/Kubernetes skew, API deprecations, workload identity and Pod Security behavior                                                                                               |
| Packaging/GitOps      | Helm and Argo CD                                           | TBD                                                                                                                                  | Supported Kubernetes range; render/schema/sync/rollback tests                                                                                                                                       |
| Telemetry             | OpenTelemetry SDK/Collector                                | Python SDK/exporter 1.44.0; Collector 0.159.0 image digest `sha256:1f2c54a30e713fac6b3ae77a1ec84010c2007e29ced8ec666214fc2f6739c1cc` | OTLP HTTP endpoint validation, local request metrics and collector health passed; dashboard/retention checks remain later                                                                           |
| Metrics/logs/traces   | Prometheus, Grafana, Loki, Tempo                           | TBD                                                                                                                                  | Supported integration matrix, retention and query/dashboard tests                                                                                                                                   |
| Sandbox               | Firecracker on KVM Linux; policy-limited rootless fallback | TBD                                                                                                                                  | Record Firecracker/kernel/rootfs digests; test fail-closed downgrade and actual hardening profiles                                                                                                  |
| Code intelligence     | ripgrep, tree-sitter, selected LSP servers                 | TBD                                                                                                                                  | Define supported languages; pin grammars/servers; parser/LSP corpus tests                                                                                                                           |
| API runtime image     | Python slim runtime                                        | `python:3.13.13-slim-bookworm` digest `sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f`                      | `pnpm build` built `asdo-api:local` successfully from the generated wheel with non-root runtime user                                                                                                |
| Web runtime image     | Node slim runtime                                          | `node:24.18.0-bookworm-slim` digest `sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d`                        | `pnpm build` built `asdo-web:local` successfully from Next standalone output with non-root runtime user                                                                                             |

## Security and supply-chain tools

| Function               | Candidate                                                      | Version/digest state | Required validation                                                           |
| ---------------------- | -------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------- |
| SAST                   | Semgrep Community; CodeQL when legally/operationally available | TBD / blocked        | Known-vulnerable fixtures; licensing/availability decision; SARIF contract    |
| Secret scanning        | Gitleaks                                                       | TBD                  | Seeded secret fixtures, allowlist governance and redaction                    |
| Container/IaC scan     | Trivy                                                          | TBD                  | Database freshness/pinning policy and known-bad image/IaC fixtures            |
| SBOM                   | Syft plus CycloneDX or SPDX                                    | TBD                  | Released-image inventory completeness and schema validation                   |
| Vulnerability analysis | Grype                                                          | TBD                  | SBOM/image matching, severity policy and exception expiry                     |
| Signing/attestation    | Cosign                                                         | TBD                  | Approved keyless/managed-key trust model, identity and admission verification |

## Approved platform profiles requiring exact-version selection

| Profile             | Decision needed                                                                        | Compatibility impact                                                                                 |
| ------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Developer OS        | Linux, macOS and Windows through WSL2                                                  | Firecracker is Linux/KVM-specific; local fallback and task portability differ                        |
| CPU architecture    | Linux `amd64` and `arm64`; Firecracker may start `amd64`                               | Image availability, Firecracker, LSP and scanner binaries; arm64 stays on roadmap                    |
| Kubernetes/cloud    | Docker Compose/kind local; AWS EKS reference in `eu-central-1`/`eu-west-1` DR          | Cloud-neutral modules plus EKS storage, ingress, workload identity, KMS and policy validation        |
| Git provider        | GitHub first; GitLab required before final release                                     | Common contract, app/token model, webhooks, checks and dedicated test organizations                  |
| Model/embedding     | OpenAI/Anthropic/Gemini-compatible, vLLM, dev Ollama; BGE-M3/E5/commercial embeddings  | Classification/residency/retention policy, offline route, tokenizer/vector dimension and re-indexing |
| Supported languages | Tier one TS/JS, Python, Go, Java/Kotlin; additional approved language list in ADR-0003 | Pin grammars/LSPs; publish limitations; test parsers, symbols, sandboxes and evaluation datasets     |
| Client browsers     | Latest two stable Chrome, Firefox, Edge and Safari                                     | Playwright projects, accessibility, CSP and compatibility-window verification                        |

## Approved compatibility constraints

- APIs support the current and previous major versions, with additive changes within a major and
  180-day breaking-change notice.
- Database changes support at least one rolling-deployment version boundary.
- Temporal changes replay deterministically against retained histories.
- Production AWS and DR profiles, data residency and environment/account isolation follow ADR-0002
  and ADR-0004.
- Quality/security thresholds and blocking provenance/image conditions follow ADR-0005.
- Releases and digests not owned by the active milestone remain `TBD` until official-source
  verification immediately before approved dependency selection.

## Executed compatibility evidence

| Scope                    | Command/evidence                                                                                    | Result                                                                                                                                                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 0A workspace       | `pnpm verify` on 2026-08-18                                                                         | Passed: format, lint, strict typecheck, 19 unit tests (7 TypeScript and 12 Python), measured packages/services at 100% coverage, builds and security checks                          |
| Runtime observation      | `node --version`; `pnpm --version`; `uv --version`; `uv run python --version`                       | 24.18.0; 11.22.0; 0.11.7; CPython 3.13.13                                                                                                                                            |
| PostgreSQL manifest      | `docker buildx imagetools inspect postgres:18.4`                                                    | OCI index digest pinned above; linux/amd64 and linux/arm64 manifests present                                                                                                         |
| Local PostgreSQL task    | `pnpm db:up`                                                                                        | Digest-pinned container created and reached healthy state                                                                                                                            |
| Phase 0B Python packages | `python -m pip index versions SQLAlchemy`; equivalent Alembic/asyncpg queries; `uv.lock` inspection | Latest stable releases selected and locked: SQLAlchemy 2.0.52, Alembic 1.19.1, asyncpg 0.31.0                                                                                        |
| Phase 0B migration       | `pnpm db:migrate`                                                                                   | Alembic upgraded PostgreSQL to `20260818_0001`; local application role provisioned with no RLS bypass                                                                                |
| Phase 0C workspace       | `pnpm verify` on 2026-08-18                                                                         | Passed format, lint, strict TypeScript/Python checks, 7 TypeScript unit tests at 100% package coverage, 36 Python unit tests at 91.57% coverage, builds and security checks          |
| Phase 0C database        | `pnpm test:integration` on 2026-08-18                                                               | Passed one-head check at `20260818_0002`, upgrade/downgrade/upgrade, real PostgreSQL role, forced-RLS, wrong-tenant CRUD/audit isolation, append-only audit tamper rejection         |
| Phase 0D workspace       | `pnpm verify` on 2026-08-19                                                                         | Passed format, lint, strict TypeScript/Python checks, 7 TypeScript unit tests, 50 Python unit tests at 91.27% coverage, build/image builds, container HTTP smoke and security target |
| Phase 0D platform        | `pnpm dev-infra`; `pnpm deploy:local`; `pnpm smoke:test`; `pnpm test:security` on 2026-08-19        | Passed Compose health for PostgreSQL/OPA/OTel Collector, static Helm/Argo security validation, API health/metrics smoke, API/web container HTTP smoke and local secret/audit checks  |

The Phase 0B evidence covers the initial relational organization store only. pgvector,
background-worker context, and every future cache/object/event/log/metric store must repeat the
tenant-contamination suite in their owning milestones.

## Update and release rules

1. Record exact versions only after official-source verification and Phase 0 approval.
2. Use automated update proposals, but require lockfile diff, test/security evidence and human
   review.
3. Test database, workflow, API/event/agent-contract and provider compatibility across the approved
   window.
4. Verify image signatures and digests at admission; a registry tag is descriptive only.
5. Record every non-open-source dependency, why it is used and its open-source alternative.
6. Revalidate the matrix at each milestone and release; never infer compatibility merely because
   installation succeeds.
