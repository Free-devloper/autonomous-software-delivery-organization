# Phase 0B Persistence and Tenancy Contract

**Status:** Verified for the initial relational organization store; deferred scope is explicit
below  
**Baseline:** `project_doc.txt` plus decision addendum 1.0, approved 2026-08-18  
**Scope:** PostgreSQL/Alembic foundation, organization tenant model, row-level security (RLS),
migration discipline, and database isolation evidence

## Boundary and acceptance criteria

Phase 0B establishes the database security boundary required before identity and tenant-facing
features. It does not implement OIDC, RBAC, audit, cache/object/event/telemetry tenancy, residency
routing, retention jobs, or Kubernetes deployment. Those remain assigned to their later milestones.

Phase 0B is acceptable only when all of the following execute successfully against PostgreSQL:

1. Alembic upgrades a new database from `base` to exactly one `head`.
2. The schema can be downgraded to `base` and upgraded again in a disposable database.
3. The application role is neither superuser nor `BYPASSRLS`, and cannot disable RLS.
4. Missing, malformed, and wrong organization context fail closed.
5. Two organizations can create and read their own records while neither can read, insert, update,
   or delete the other's records through direct SQL or the pooled application path.
6. Transaction-local context is cleared on commit and rollback, including when a pooled connection
   is reused.
7. Migration SQL and metadata remain type/lint clean and the Phase 0A verification suite does not
   regress.

Passing code inspection or SQLite tests is not database-isolation evidence.

## Executed evidence

Executed on 2026-08-18:

| Command                 | Result                                                                                                                                                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pnpm db:up`            | Digest-pinned PostgreSQL 18.4 reached healthy state on the loopback-only port                                                                                                                                                                          |
| `pnpm db:migrate`       | Alembic applied revision `20260818_0001` and provisioned a separate local application role without superuser or RLS-bypass attributes                                                                                                                  |
| `pnpm test:integration` | Passed exactly-one-head check, upgrade/downgrade/upgrade and one real PostgreSQL test covering unscoped registry denial, forced RLS, missing/invalid context, wrong-tenant CRUD and commit/rollback context reset through a reused one-connection pool |
| `pnpm verify`           | Current aggregate suite passed formatting, lint, strict TypeScript/Python checks, 7 TypeScript unit tests at 100% package coverage, 36 Python unit tests at 91.57% coverage, builds, secret scan and production dependency audit                       |

The integration database is dedicated to this runner. The normal `db-down` operation retains its
volume.

## Data contract

### Identifiers and organization registry

- Tenant identity is an application-generated UUID named `organization_id`; database sequence IDs,
  human-readable slugs, issuer claims, and request fields are never the authorization boundary.
- The `organizations` registry uses its own UUID `id` as the organization identity. Tenant-owned
  rows use a non-null `organization_id` foreign key to that registry.
- IDs are immutable. Mutable display names and slugs are attributes, not security principals.
- Primary and foreign keys use native PostgreSQL `uuid`. Timestamps use timezone-aware
  `timestamptz`, are stored in UTC, and receive database-side defaults where appropriate.
- Tenant-owned uniqueness includes `organization_id` unless global uniqueness is an explicitly
  reviewed invariant. Tenant foreign keys use `(organization_id, id)` where that prevents a child
  row from referencing another organization's parent.

The initial migration contains an organization registry plus `organization_configurations`, a real
tenant-owned record that proves the boundary. Later domain tables must reuse the same mixin/DDL
conventions rather than relying on ORM filters as a substitute for RLS.

### RLS policy

Every tenant table, including the organization registry when tenant-scoped reads are exposed, uses
both `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`. Policies apply the organization
predicate to visibility and new row values:

```sql
USING (organization_id = nullif(current_setting('asdo.organization_id', true), '')::uuid)
WITH CHECK (organization_id = nullif(current_setting('asdo.organization_id', true), '')::uuid)
```

For `organizations`, the predicate compares `id` rather than `organization_id`. A missing setting
evaluates to no rows; an empty setting evaluates to no rows; an invalid UUID raises an error. The
database owner and migration connection are never used for application traffic.

### Roles and privileges

- A migration/owner identity owns schema objects and is confined to migration workflows.
- The runtime application identity is `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, and
  `NOBYPASSRLS`. It receives only the required schema/table/sequence privileges.
- Tests assert role attributes from PostgreSQL catalogs. Managed-service role provisioning may be
  external to Alembic, but migrations still create and force policies on every tenant table.
- Runtime credentials are never committed. Compose credentials are explicitly local/test-only and
  must not be reused outside disposable development databases.

## Transaction and pooling contract

Tenant context is established only inside an open transaction, before tenant SQL, with the
equivalent of:

```sql
SELECT set_config('asdo.organization_id', :organization_id, true);
```

The third argument must be `true` so the value is transaction-local. The trusted service boundary
supplies the UUID; repositories do not accept a caller-provided tenant override. A missing context,
attempt to issue tenant SQL outside that scope, nested scope for a different organization, or
context setup failure aborts the transaction. Commit, rollback, cancellation, and exception paths
must return the connection without organization state.

Phase 0C will derive organization membership from validated identity and deterministic policy. Phase
0B's context API is therefore an internal trusted boundary, not an authorization mechanism by
itself.

## Migration discipline

1. Each revision has one predecessor and descriptive, deterministic upgrade/downgrade operations; CI
   rejects multiple heads.
2. Revisions use expand-migrate-contract. Additive schema must support the current and immediately
   previous application version. New required columns are added nullable or with a safe default,
   backfilled separately, then constrained only after mixed-version evidence.
3. Destructive or data-rewriting contract steps are never combined with the expand deployment.
   Production downgrade is not implied by a disposable round-trip test; recovery uses a reviewed
   forward fix or restore plan.
4. RLS is enabled and forced in the same revision that introduces a tenant table. A tenant table is
   not exposed to the runtime role between table creation and policy enforcement.
5. Autogenerate output is reviewed. Handwritten policy and privilege SQL is explicit, quoted safely,
   and covered by catalog assertions.
6. Migration tests use an isolated database, verify both clean install and round trip, and never
   target a developer-selected or production database implicitly.

## Verification commands

The root task surface is the supported entry point once the Phase 0B implementation lands:

```sh
make db-up
make db-migrate
make test-integration
make db-down
make verify
```

`db-down` retains the local database volume by default. Destructive volume removal is deliberately
not part of the normal task surface. The integration runner must provision unique test state and
clean only that state.

## Requirement coverage and deferred work

| Requirement               | Phase 0B evidence                                                                         | Deferred portion                                                                              |
| ------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| PROV-005                  | SQLAlchemy/Alembic configuration, typed models and migration tests                        | OIDC/RBAC and later API errors remain 0C                                                      |
| PROV-010 / DEC-TEN-002    | Forced RLS, role assertions, direct-SQL and pooled cross-tenant tests                     | Vector/background stores repeat the suite when introduced                                     |
| PROV-018 / DEC-COMPAT-002 | Single-head, clean install and disposable round-trip tests; additive migration policy     | Mixed old/new production release proof remains 6A                                             |
| DEC-TEN-001               | Shared-control-plane organization model uses provider-neutral application code            | Dedicated Helm/profile equivalence remains 0D                                                 |
| DEC-TEN-003               | SQL tenancy convention is established                                                     | Cache, object, event, vector, log and metric scoping remains 0B-0D and later store milestones |
| DEC-DATA-001              | Organization record can carry approved region metadata without implementing routing       | Storage placement, replication and egress enforcement remain 0D and later adapters            |
| DEC-CLASS-001             | Database enum/constraint vocabulary may be established only if exercised by a real record | Full policy enforcement remains 0C-4D                                                         |
| DEC-RET-001/002           | Retention categories may be represented only for real Phase 0B records                    | Lifecycle deletion, legal hold and WORM evidence remains with owning milestones               |

Phase 0B must not mark a deferred requirement verified merely because its future-facing column or
policy vocabulary exists.
