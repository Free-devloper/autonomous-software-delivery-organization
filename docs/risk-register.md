# Risk Register

**Status:** Active  
**Date:** 2026-08-19  
**Basis:** `project_doc.txt`, repository assessment and pre-implementation threat analysis

Likelihood and impact are inherent estimates until architecture, scale and compliance decisions are
approved. `P0` risks must be resolved or have an explicit, time-bound acceptance before relevant
work begins. Risk acceptance never authorizes a model or agent to bypass deterministic controls.

| ID / priority | Risk                                                                                                                                |  Likelihood |   Impact | Mitigation and exit condition                                                                                                              | Owner / trigger                                           |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------: | -------: | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| R-01 / P1     | Authoritative `project_doc.txt` lacks formal requirement IDs, increasing traceability-drift risk                                    |      Medium |     High | Maintain stable `PROV-*`/`DEC-*` IDs, baseline versioning and reviewer audits through every milestone                                      | Coordinator + reviewer / requirement change               |
| R-02 / P0     | Approved cloud, topology, tenancy, compliance, residency, retention, SLO, RPO and RTO constraints may be implemented inconsistently |      Medium | Critical | Enforce ADR-0002/0004 through contracts, policy, tests and architecture review                                                             | Coordinator/product/compliance / every milestone          |
| R-03 / P0     | Firecracker infrastructure is unavailable and rootless fallback is used beyond an accepted risk class                               |        High | Critical | Confirm Linux capacity; define mandatory microVM cases; block untrusted execution until actual profiles pass                               | Platform + security / Phase 3                             |
| R-04 / P0     | Cross-tenant leakage via RLS bypass, pooled context, vector search, cache, objects, events, telemetry or backups                    |        High | Critical | Force RLS for app roles, transaction-local tenant context, tenant-scoped non-SQL stores and exhaustive cross-tenant tests                  | Backend + testing + reviewer / first tenant store         |
| R-05 / P0     | Approval replay/confusion, self-approval, stale privilege or digest substitution authorizes the wrong action                        |        High | Critical | Formal state machine; atomic verify-and-act; bind tenant/run/repo/commit/digest/action/environment/scope/expiry/policy; SoD property tests | Workflow + testing + reviewer / first approval            |
| R-06 / P0     | Repository/issue prompt injection changes policy, tool scope or secret access                                                       |        High | Critical | Treat content as data; immutable system policy; deterministic tool gateway; structured output and adversarial evaluation                   | Agents + security/testing / first model retrieval         |
| R-07 / P0     | Sandbox escape exposes host, cluster, cloud metadata, sockets, mounts, network or other tenants                                     | Medium-High | Critical | Firecracker, dedicated nodes, deny egress, no host sockets/mounts, least privilege and actual escape regression suite                      | Sandbox/platform + reviewer / untrusted execution         |
| R-08 / P0     | Secrets leak through models, subprocesses, patches, logs, traces, artifacts or backups                                              |        High | Critical | Short-lived scoped injection, no model exposure by default, source/sink redaction, canary scans and rapid revocation                       | Platform/security / first credential use                  |
| R-09 / P1     | External model/embedding provider processes private code contrary to contract, residency or retention policy                        |        High | Critical | Approve provider/data-class matrix, zero-retention/no-training settings, region routing and local/offline route                            | Product/compliance + agents / provider choice             |
| R-10 / P1     | SCM token/webhook compromise or replay causes false state and duplicate effects                                                     |      Medium |     High | Least-scope app tokens, raw-body signatures, replay store, idempotency, rotation and reconciliation tests                                  | Repository/testing / SCM integration                      |
| R-11 / P1     | Mutable refs or mixed/stale indexes cause work and approval against different commits                                               | Medium-High |     High | Carry immutable provider/repository/commit identity through every contract and index; force-push race tests                                | Repository/indexer / Phase 1                              |
| R-12 / P1     | Dependency confusion, malicious install scripts, compromised images or signature bypass compromise supply chain                     |        High | Critical | Lockfiles, trusted registries, isolated install, digest pins, SBOM/scans, Cosign verification and admission policy                         | Platform/security / first dependency/image                |
| R-13 / P1     | Workflow replay or crash windows duplicate PR, deployment, migration or rollback side effects                                       |      Medium | Critical | Durable idempotency keys, unique constraints, outbox/inbox, workflow versioning and failure-injection tests                                | Workflow/testing / first external effect                  |
| R-14 / P1     | OIDC or claim/session mistakes cause escalation or stale-session approval                                                           |      Medium | Critical | Strict issuer/audience/algorithm/time validation, server-side membership, revocation, fresh-auth policy and negative matrix                | Identity/testing/reviewer / Phase 0C                      |
| R-15 / P1     | SSRF, path/link escape, command injection or unsafe deserialization compromises controllers/internal networks                       |        High | Critical | Safe fetch/egress layer, descriptor-based containment, argument-vector APIs, safe schemas and adversarial tests                            | Backend/sandbox/repository / new input boundary           |
| R-16 / P1     | Migration/rollback mismatch causes irreversible data loss or outage                                                                 |      Medium | Critical | Expand-migrate-contract, mixed-version tests, PITR, restore rehearsal and explicit irreversible limitations                                | Data/platform/reviewer / each migration                   |
| R-17 / P1     | Backup, keys or dependencies fail during recovery and unknown objectives cannot be met                                              |      Medium | Critical | Define RPO/RTO; encrypted isolated backups; complete dependency inventory; scheduled measured restore/DR exercises                         | Platform/testing / before production data                 |
| R-18 / P1     | Overprivileged CI, Argo, Kubernetes, registry or signing identity crosses environments                                              |      Medium | Critical | Separate environment identities/trust roots, least RBAC, protected GitOps and admission/credential-boundary tests                          | Platform/reviewer / delivery design                       |
| R-19 / P2     | Resource exhaustion, parser bombs, agent loops or noisy tenants cause outage or uncontrolled spend                                  |        High |     High | Quotas, cgroups, bounded queues/concurrency, cancellation, budgets, backpressure and load/fuzz tests                                       | Platform/agents/indexer / before tenant load              |
| R-20 / P2     | XSS or log/telemetry injection from repository content compromises users/operators                                                  |        High |     High | Escaped/sanitized rendering, CSP, structured logs, telemetry scrubbing and hostile-content browser tests                                   | Frontend/backend/testing / first source UI                |
| R-21 / P0     | Immutable audit may be too weak to resist privileged tampering or support nonrepudiation                                            |      Medium |     High | Define append-only/tamper evidence, time source, WORM requirements, access separation, retention/export and verification before 0C         | Security/compliance / Phase 0 entry                       |
| R-22 / P2     | No provider test organizations leave GitHub/GitLab behavior mock-only                                                               |      Medium |     High | Use contract servers during development; require dedicated-org evidence before provider support claim                                      | User + repository/testing / Phases 1 and 5                |
| R-23 / P2     | Provider-neutral fallback silently changes security/data-processing behavior                                                        |      Medium |     High | Typed capability/policy matrix; forbid unauthorized fallback; audit provider selection; contract tests                                     | Agents/compliance / gateway design                        |
| R-24 / P0     | Approved mutation, coverage, retrieval/evaluation, compatibility and vulnerability gates may drift or be bypassed                   |      Medium |     High | Encode ADR-0003/0005 thresholds and exception metadata/expiry in CI and policy; regression-test gate changes                               | Testing/security/reviewer / Phase 0 and every gate change |
| R-25 / P0     | Missing Git history prevents change attribution and preservation checks                                                             |     Certain |   Medium | Confirm new-repository intent before Phase 0; initialize only after approval and establish ignore/signing/branch policy                    | User + coordinator / Phase 0 entry                        |
| R-26 / P2     | Broken local Windows sandbox helper undermines expected automation isolation                                                        |     Certain |   Medium | Repair helper or document a supported Linux/WSL execution environment before sandbox-dependent local checks                                | User/platform / development bootstrap                     |

## Risk acceptance rules

- A risk acceptance must identify the exact risk, affected scope/environment, accountable human,
  rationale, compensating controls, expiry and re-review trigger.
- Critical security risks cannot be accepted implicitly through build approval.
- Missing verification infrastructure results in `Blocked` or `Planned`, never `Verified`.
- Review this register at milestone start/end and whenever architecture, provider, threat boundary
  or requirement baselines change.

## Decision update - 2026-08-18

The following design uncertainties are resolved by accepted ADRs, but their implementation risks
remain open until verified:

| Risks                  | Approved treatment                                                                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R-02, R-17, R-18       | AWS/EKS reference topology, account/environment isolation, certified SLO/capacity/cost targets, warm DR, RPO/RTO and exercise cadence are fixed by ADR-0002. |
| R-03, R-07             | Dedicated KVM/Firecracker production sandbox pools and fail-closed downgrade behavior are fixed by ADR-0005.                                                 |
| R-04, R-08, R-09, R-20 | SaaS/dedicated tenancy, classifications, residency, retention, encryption and external-model restrictions are fixed by ADR-0004.                             |
| R-05, R-14, R-21, R-24 | Roles, MFA freshness, approval binding/expiry/SoD/break-glass, WORM audit and measurable quality/security gates are fixed by ADR-0005.                       |
| R-10, R-11, R-22, R-23 | GitHub-first/GitLab provider contracts, dedicated live verification and model/embedding/offline policies are fixed by ADR-0003.                              |
| R-12, R-16             | Compatibility, provenance, immutable images and rolling-version requirements are fixed across ADR-0002, ADR-0003 and ADR-0005.                               |

The requirements baseline, GitHub organization and Phase 0 build approval are resolved. R-25 remains
open because remote GitHub creation/protection evidence requires an authenticated `gh` session, and
the local sandbox-helper defect R-26 remains. No risk is closed merely by documenting its treatment;
closure requires implementation and passing evidence.

## Phase 0B risk update - 2026-08-18

- R-04 is mitigated and verified for the initial PostgreSQL `organization_configurations` store: the
  real-database suite passed forced-RLS, least-privilege role, wrong-tenant CRUD, missing/invalid
  context, commit/rollback and pooled-connection reuse assertions. R-04 remains open for pgvector,
  background jobs, cache, objects, events, telemetry and backups until each is implemented and
  passes the same contamination matrix.
- R-16 remains open. The initial Alembic revision has one head and passed a disposable
  upgrade/downgrade/upgrade, but mixed old/new application compatibility, backup/PITR and production
  forward-fix/restore rehearsals belong to later release and recovery milestones.
- Local Compose credentials and the migration superuser are test-only. Production role provisioning,
  secret delivery, encrypted transport/storage and separate environment keys remain 0D work and must
  not reuse these credentials.

## Phase 0C risk update - 2026-08-18

- R-14 is partially mitigated for local API JWT verification: issuer, audience, RS256 JWKS key
  selection, organization claim extraction and deterministic role authorization have passing unit
  tests. The risk remains open for production OIDC discovery/JWKS refresh, logout/revocation, MFA
  freshness, server-side membership synchronization and the complete role-action matrix.
- R-21 is partially mitigated for PostgreSQL audit storage: local tests cover tenant-scoped audit
  hash chaining and database-triggered update/delete rejection. The risk remains open for signed
  checkpoints, trusted timestamps, WORM replication, offline verification, retention and privileged
  operator separation.
- R-05 remains open. No approval workflow, separation-of-duties state machine, digest-bound approval
  record or replay/confusion property suite exists yet.
- R-24 is currently mitigated for the implemented local unit coverage gate: `pnpm verify` passed
  with Python coverage above the 90% Phase 0 threshold. Mutation, changed-line coverage, security
  recall and exception governance remain later milestones.

## Phase 0D risk update - 2026-08-19

- R-12 is partially mitigated for local Phase 0D image discipline: API and web Dockerfiles use
  digest-pinned base images and non-root users, the API image installs hash-checked requirements
  derived from `uv.lock`, the web image builds its standalone output in Linux, and `pnpm build`
  successfully produced local images. SBOM generation, vulnerability image scanning, provenance
  signing and admission enforcement remain open.
- R-18 is partially mitigated by static Helm/Argo manifests with non-root pod security contexts,
  disabled service-account token automounting, resource limits, liveness/readiness probes,
  release-scoped selectors, generated internal service URLs, PDB, HPA and default-deny NetworkPolicy
  with telemetry/DNS allowances. The risk remains open until Helm rendering, cluster apply,
  admission policy and environment identity boundaries are tested in a real local/staging cluster.
- R-20 is partially mitigated for backend telemetry and logs: telemetry tests cover bounded route
  labels, validated correlation IDs, JSON log escaping, sanitized exception metadata and redaction
  for common credential URL, bearer-token and secret-assignment shapes. Browser rendering of
  untrusted content, CSP and hostile diff/SARIF fixtures remain later milestones.
- R-24 is reinforced for Phase 0D local gates: `pnpm verify`, `pnpm test:security`,
  `pnpm test:integration`, `pnpm deploy:local`, `pnpm dev-infra`, `pnpm smoke:test` and container
  HTTP smoke passed. Mutation, scanner recall, SBOM/signing and external CI enforcement remain open.
- R-26 remains open in this Windows shell because GNU Make and several platform/security CLIs are
  not installed. The committed Makefile exists, but Phase 0D evidence used equivalent `pnpm`
  commands. `helm`, `kind`, `opa`, `cosign`, `syft`, `trivy` and `gitleaks` must be installed or run
  in a supported Linux/WSL/CI profile before their evidence can be claimed.
