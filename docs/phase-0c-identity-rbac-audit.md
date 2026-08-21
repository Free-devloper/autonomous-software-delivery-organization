# Phase 0C Identity, RBAC and Audit Contract

**Status:** Verified for the local API identity, deterministic authorization and PostgreSQL audit
foundation  
**Baseline:** `project_doc.txt` plus decision addendum 1.0, approved 2026-08-18  
**Scope:** Keycloak-compatible OIDC token verification, organization membership extraction,
deterministic role authorization for the existing organization-configuration API, and append-only
tenant-scoped audit persistence

## Boundary and acceptance criteria

Phase 0C establishes the first authenticated API boundary and audit substrate. It does not implement
MFA freshness, approval workflows, break glass, WORM object-lock replication, audit export/search,
OPA bundles, production IdP discovery, or Kubernetes delivery. Those remain assigned to 0D, 5B, 6B
and later milestones.

Phase 0C is acceptable only when all of the following execute successfully:

1. OIDC settings fail configuration validation unless issuer, audience and JWKS are supplied
   together.
2. Protected organization routes fail closed without configured identity, bearer token or active
   organization header.
3. RS256 JWTs are verified against configured issuer, audience and JWKS; wrong issuer, audience and
   key ID are rejected.
4. Organization membership and ASDO roles are derived from a configured claim, not request body or
   model output.
5. Deterministic policy permits only explicitly allowed roles for protected actions.
6. Audit events are recorded in transaction-local tenant scope with canonical payload hashes and
   per-organization hash chaining.
7. PostgreSQL RLS prevents cross-tenant audit visibility/inserts and database triggers reject audit
   update/delete attempts.
8. Phase 0A/0B verification does not regress.

## Executed evidence

Executed on 2026-08-18:

| Command                                                                                                | Result                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv run pytest services -m unit --maxfail=5`                                                           | Passed 34 selected unit tests before coverage-hardening changes.                                                                                                                                          |
| `uv run ruff check services/api`                                                                       | Passed.                                                                                                                                                                                                   |
| `uv run mypy services`                                                                                 | Passed with no issues in 23 source files.                                                                                                                                                                 |
| `uv run pytest services -m unit --cov=autonomous_sdo_api --cov-branch --cov-fail-under=90 --maxfail=5` | Passed 36 selected unit tests; total Python coverage 91.56%.                                                                                                                                              |
| `pnpm verify`                                                                                          | Passed formatting, lint, strict TypeScript/Python checks, 7 TypeScript unit tests at 100% package coverage, 36 Python unit tests at 91.57% coverage, builds, secret scan and production dependency audit. |
| `pnpm test:integration`                                                                                | Passed Alembic exactly-one-head check for `20260818_0002`, downgrade to base, upgrade to head, autogenerate check, and the real PostgreSQL tenant/audit RLS suite against digest-pinned PostgreSQL 18.4.  |

The current Git worktree has no commits, so this evidence is tied to the local file state rather
than an immutable commit. A commit or tree digest must be recorded before evidence can support a
remote phase gate.

## Implemented contract

- `Settings` validates OIDC issuer, audience, JWKS and organization-claim settings as one coherent
  configuration unit.
- `OidcTokenVerifier` accepts only RS256 JWTs signed by a configured JWK and carrying the configured
  issuer, audience, subject, expiry, issued-at and organization-access claim.
- `OrganizationContext` contains organization ID, actor ID and ASDO roles. The API resolves it from
  a bearer token plus `X-ASDO-Organization-ID`; missing identity remains fail-closed.
- `AuthorizationPolicy` maps actions to allowed roles using deterministic code. The existing
  organization-configuration read is allowed for owner, organization administrator, auditor,
  read-only viewer and service account.
- `audit_events` is a tenant-scoped PostgreSQL table protected by forced RLS. The runtime app role
  receives select/insert only, and database triggers reject update/delete attempts even from the
  migration owner.
- `AuditEventService` records canonical SHA-256 payload hashes and per-organization chained event
  hashes inside a tenant-scoped transaction.

## Deferred work

- Production OIDC discovery/JWKS refresh, logout/revocation, MFA freshness and server-side
  membership synchronization remain hardening work before production use.
- Approval, separation-of-duties, break-glass and purpose-bound deploy/rollback authorization remain
  later milestones.
- WORM retention, signed checkpoints, trusted timestamps, offline verification, audit search/export
  and DR replication remain 0D, 6B and operational-readiness work.
- OPA policy runtime and policy-bundle fail-closed behavior remain 0D/5B.
- GitHub repository creation/protection and CI execution evidence remain blocked on authenticated
  provider access.
