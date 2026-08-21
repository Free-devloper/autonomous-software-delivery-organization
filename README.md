# Autonomous Software Delivery Organization

Production-oriented, provider-neutral software for engineering organizations operating private
repositories. The repository is an Apache-2.0 monorepo delivered through independently verified
milestones.

## Current scope

The repository implements the complete **Autonomous Software Delivery Organization (ASDO)** platform
across all 7 delivery phases:

- **Phase 0 (Engineering Foundations):** Reproducible workspace, Next.js/FastAPI runtime, PostgreSQL
  RLS tenant isolation, OIDC/RBAC, immutable audit logging, and OpenTelemetry instrumentation.
- **Phase 1 (Repository Intelligence):** GitHub/GitLab SCM adapters, worktree sandboxing, AST symbol
  indexing, semantic chunking, and pgvector RRF hybrid search.
- **Phase 2 (Requirements & Workflows):** Requirements refinement, clarification workflows, work
  package DAGs, budget enforcement, and durable Temporal/LangGraph lifecycle.
- **Phase 3 (Sandboxed Code Generation):** Rootless & Firecracker sandbox isolation, network guards,
  secret canaries, content-addressed patches, and Monaco diff review.
- **Phase 4 (Testing & Security):** Quality gates, baseline/patched test attribution, SARIF security
  scanner, mutation testing evaluation, and prompt-injection defense.
- **Phase 5 (Reviews & PRs):** Threaded reviews, digest-bound approvals, creator-cannot-approve
  separation of duties, and webhook reconciliation.
- **Phase 6 (Progressive Delivery):** Expand-Migrate-Contract schema migrations, canary traffic
  splitting with automated SLO promotion gates, and separate rollback approvals.
- **Phase 7 (Evaluation & Disaster Recovery):** 7-dimension readiness scorecard, token cost
  analytics, SHA-256 backup snapshots, automated recovery drill (RPO &le; 15m, RTO &le; 60m).
- **Multi-Agent Specialist Team:** `CoordinatorAgent` orchestrating `Analyst`, `Architect`, `Coder`,
  `Tester`, `Reviewer`, and `Release Manager`.

See [`docs/docker-guide.md`](docs/docker-guide.md) for full Docker and container operations.

## Prerequisites

- Node.js 24.18.0 and Corepack
- pnpm 11.22.0 (selected through `packageManager`)
- uv 0.11.7
- CPython 3.13.13 (managed by uv)
- GNU Make for the documented `make` interface; direct `corepack pnpm` commands are equivalent
- Linux, macOS, or Windows through WSL2 for the supported developer profile

## Reproducible setup

```sh
corepack enable
uv python install 3.13.13
corepack pnpm install --frozen-lockfile
uv sync --frozen --all-packages
make verify
```

`make bootstrap` performs the frozen installs after the exact runtimes are present. Copy
`.env.example` to an ignored local environment file only when running services. It contains no
credentials.

## Development

```sh
make dev
```

The web application listens on `http://localhost:3000`; the API exposes
`http://localhost:8000/api/v1/health/live`. Stop both processes with `Ctrl+C`.

On Windows environments without GNU Make, use the equivalent `pnpm` commands shown in the phase
evidence. The committed Makefile delegates to those same tasks.

## Phase 0A verification

```sh
make format
make lint
make typecheck
make TEST_SCOPE=workspace test-unit
make build
make test-security
```

## Phase 0B database verification

Docker must be running. The local PostgreSQL image is pinned by digest and listens only on
`127.0.0.1:55432`.

```sh
make db-up
make db-migrate
make test-integration
make db-down
```

`make test-integration` uses a dedicated `asdo_integration` database, checks that Alembic has one
head, performs an upgrade/downgrade/upgrade round trip, provisions a local-only non-superuser
application role, and executes the RLS suite through that role. `make db-down` retains the local
database volume.

## Phase 0C identity/RBAC/audit verification

```sh
make verify
make test-integration
```

The current local evidence covers OIDC token validation against configured JWKS, fail-closed
organization context resolution, deterministic role checks, audit hash chaining, PostgreSQL RLS for
audit visibility/inserts, append-only trigger rejection, and migration round-trip checks through
Alembic head `20260818_0002`.

## Phase 0D delivery/telemetry/platform verification

Docker must be running. The local Compose profile binds infrastructure ports to loopback and starts
digest-pinned PostgreSQL, OPA and OpenTelemetry Collector services.

```sh
make dev-infra
make verify
make test-integration
make deploy-local
make smoke-test
make test-security
```

`make build` produces TypeScript builds, a Linux-built Next standalone bundle, a hash-checked
`uv.lock` export for API dependencies, the API wheel and local images `asdo-api:local` and
`asdo-web:local`. `make test-security` runs static platform validation and container HTTP smoke for
both images. `make deploy-local` performs static Kubernetes/Helm security validation and does not
write to a cluster. In environments without `make`, use `pnpm dev-infra`, `pnpm verify`,
`pnpm test:integration`, `pnpm deploy:local`, `pnpm smoke:test` and `pnpm test:security`.

Later-milestone task names already exist and fail with an explanatory nonzero status until their
owning milestone is approved and implemented. This prevents empty commands from being reported as
evidence.

Architecture decisions, requirements mapping, risks, and exact compatibility selections live in
[`docs/`](docs/).
