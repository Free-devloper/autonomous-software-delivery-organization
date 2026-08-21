# Threat Model

**Status:** Active; Phase 0B through 0D local controls are partially implemented and verified  
**Date:** 2026-08-19  
**Method:** Asset/trust-boundary review with STRIDE-style threat analysis

The authoritative requirements baseline is `project_doc.txt` plus decision addendum version 1.0.
Material deployment, tenancy, compliance, provider, sandbox, approval, quality and audit decisions
were approved on 2026-08-18 and are recorded in ADR-0001 through ADR-0005. This document defines the
minimum security direction required before execution functionality is exposed.

## Security objectives

1. Preserve tenant isolation and confidentiality for private code, requirements, indexes, prompts,
   state, artifacts, telemetry and backups.
2. Permit consequential actions only for currently authorized humans under deterministic policy.
3. Bind approval to the exact immutable artifact and full
   tenant/run/repository/commit/action/environment/scope context.
4. Prevent model output and untrusted repository content from changing policy, authorization or tool
   scope.
5. Isolate untrusted execution from hosts, clusters, other tenants, secrets, metadata and
   unrestricted networks.
6. Preserve provenance and integrity of workflows, patches, tests, findings, releases, deployments
   and audit events.
7. Make side effects idempotent and durable work recoverable.
8. Fail closed whenever identity, tenant, policy, approval, signature or digest verification is
   incomplete.

## Assets and actors

Critical assets include identities/sessions/roles; private repositories and immutable commits;
indexes and embeddings; prompts/templates/model responses/tool calls; Temporal histories and
LangGraph checkpoints; patches/digests/tests/SARIF/SBOM/signatures/images; approvals and audit
events; provider/model/cluster/signing credentials; PostgreSQL/cache/object data and backups;
releases/deployments/rollback state; and logs/traces/metrics.

Trusted actors are trusted only within least-privilege roles: requester, reviewer, PR approver,
deployment approver, rollback approver, tenant administrator, platform/security operator and service
identities. Potentially hostile actors include anonymous users, compromised or malicious tenant
users/admins/operators, repository contributors and dependencies, compromised
providers/registries/workloads, model output, and any tenant attempting lateral access or
exhaustion.

## Trust boundaries and entry points

Principal boundaries are:

1. Browser to ingress/API/live-event stream.
2. API to OIDC identity and tenant/role claims.
3. Service-to-service typed contracts and workload identities.
4. Services to PostgreSQL/RLS, cache, object storage and vector search.
5. GitHub/GitLab APIs, webhooks, repository refs/content and provider adapters.
6. Repository/issues/retrieval content to parsers, UI, model gateway and agents.
7. Temporal/LangGraph persisted state to executing workflows.
8. Workflow/controller to sandbox, scoped worktree, runtime secrets, network and host/cluster.
9. Patch/test output to content-addressed artifact storage and approval UI/service.
10. Approved artifact to PR, registry, signing, Argo CD, Kubernetes, deployment and rollback
    effects.
11. Services to telemetry and primary data to backup/restore/DR systems.
12. Organization data to external model, embedding, SCM, storage and support providers.

Entry points include OIDC callbacks/tokens, APIs/admin configuration/live streams, webhooks/provider
responses, clone URLs/refs/issues, files/manifests/symlinks/submodules/LFS/archives,
requirements/prompts/model output/tool calls, workflow signals, sandbox commands/package managers,
patches/artifacts, approvals/PR/deploy/rollback requests, images/Helm/IaC/migrations, secret
injection, telemetry fields and restore inputs.

## Threats, required controls and verification

| ID      | Threat and impact                                                                                          | Required control direction                                                                                                                           | High-value verification                                                                                                  |
| ------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| TM-S1   | Forged/expired/wrong-audience OIDC token or bad tenant/role mapping                                        | Strict issuer/audience/signature/algorithm/time checks; PKCE/state/nonce; server-side membership; revocation and fresh auth for approvals            | Wrong issuer/key/algorithm/time/nonce, removed membership and stale-session approval tests                               |
| TM-S2   | Spoofed/replayed webhook mutates state or repeats work                                                     | Raw-body signature, delivery ID/freshness replay store, secret rotation, idempotency and reconciliation                                              | Altered body, stale/duplicate/concurrent delivery and rotation overlap tests                                             |
| TM-T1   | Mutable ref or mixed index causes planning/patch/approval against different commits                        | Resolve immutable commit once and carry provider/repo/commit through contracts, indexes and artifacts                                                | Move/force-push branch between phases; cross-commit retrieval and PR base tests                                          |
| TM-T2   | Repository/docs/tests/issues inject instructions into agents                                               | Content provenance and quoting; immutable system policy; deterministic tool/authorization gateway; validated typed outputs                           | Nested/encoded injection corpus requesting secrets, policy changes, widened paths, test deletion or self-approval        |
| TM-T3   | Digest substitution/canonicalization or TOCTOU reuses approval on changed data                             | Canonical content bytes; collision-resistant digest; full-context binding; atomic verify-and-act                                                     | Encoding/order/metadata changes, artifact swap and replay across every context field                                     |
| TM-T4   | Workflow retries/checkpoints/cancel races duplicate side effects or corrupt state                          | Deterministic versioned workflows, idempotency keys, unique constraints, outbox/inbox and guarded state machine                                      | Crash before/after effects, duplicate signals, retry storms, cancel/resume and concurrency tests                         |
| TM-T5   | Dependency confusion, malicious install, unsigned or substituted image/artifact                            | Locked dependencies, trusted registries, isolated install, digest pins, SBOM/scans, signatures/attestations and admission                            | Hostile higher version, lifecycle script, tampered lock/SBOM/signature and wrong-signer/unsigned image tests             |
| TM-R1   | Actor repudiates approval/deployment or audit is altered                                                   | Append-only/tamper-evident event containing actor, tenant, context, digest, policy version, result, correlation and trustworthy time                 | Update/delete/backdate attempts and end-to-end audit completeness checks                                                 |
| TM-I1   | Cross-tenant leakage through SQL/pools/vector/cache/object/events/telemetry/backups                        | Force RLS; transaction-local context; no bypass roles; tenant-scoped keys/auth for every non-SQL store/path                                          | Cross-tenant matrix including pooled connections, background jobs, events and restores                                   |
| TM-I2   | Secrets leak through model, environment, patches, logs, traces or artifacts                                | Short-lived least-scope injection, no model exposure by default, redaction at source/sink and rapid revoke                                           | Canary secrets across model request, subprocess, crash, patch, log, trace, artifact and backup paths                     |
| TM-I3   | External AI/storage provider receives private data against residency/retention/training policy             | Tenant/data-class provider policy, minimization, approved regions, no-training/retention controls and offline route                                  | Block disallowed provider/region/data; inspect transmitted content/config; ensure outage cannot silently change provider |
| TM-I4   | Source/issues/findings cause XSS, unsafe links, log forging or telemetry leakage                           | Text-safe rendering, sanitized Markdown, strict CSP/safe URLs, structured logs, bounded/scrubbed telemetry                                           | Hostile filenames/source/diffs/SARIF/links, control characters and sensitive error tests                                 |
| TM-I5   | SSRF from clone URLs, submodules, LFS, packages or tools reaches internal services                         | Scheme/host/port allowlists, DNS/IP revalidation, redirect limits, egress proxy/policy and metadata/internal blocking                                | DNS rebinding, redirects, encoded IPv4/IPv6, cloud metadata, Kubernetes/service DNS tests                                |
| TM-D1   | Repository/parser/build/vector/event/model workloads exhaust resources or budget                           | Tenant quotas, cgroups, bounded queues/concurrency, file/depth/time limits, cancellation/backpressure/circuit breakers                               | Fork/memory/disk bombs, huge/deep corpus, expensive query, slow event client, model loop and noisy-neighbor tests        |
| TM-D2   | Provider/IdP/DB/cache/storage/workflow outage creates retry storm or divergence                            | Explicit timeouts/backoff/circuit breakers, durable queues, idempotency, degraded modes and reconciliation                                           | Partial partition, rate limit, outage, restart/replay and backlog recovery tests                                         |
| TM-E1   | RBAC/policy failure or model claim yields privilege escalation                                             | Central deterministic policy, server-derived tenant/role, least privilege and deny on missing/malformed/unavailable policy                           | Horizontal/vertical matrix, forged fields, OPA outage/timeout and model tool-escalation tests                            |
| TM-E2   | Sandbox escapes to host/socket/mount/metadata/network/other sandbox                                        | Firecracker for untrusted code; tightly classified rootless fallback; non-root/read-only/drop caps/seccomp/AppArmor; dedicated nodes and deny egress | Actual-profile mount/socket/device/proc/sys/capability/network/metadata/cross-sandbox tests                              |
| TM-E3   | Path/link/archive/Unicode race, command injection or unsafe deserialization escapes write scope/controller | Descriptor-based containment, link revalidation, safe extraction, argument-vector APIs and schema-safe bounded serialization                         | Symlink swap, hardlink/junction, traversal/UNC/device/case/Unicode/archive/metacharacter/crafted payload tests           |
| TM-E4   | CI/Argo/Kubernetes/signing identity crosses environment or gains cluster control                           | Separate accounts/identities/trust roots, least RBAC, protected GitOps, admission policy and no wildcard secrets                                     | Staging credential against prod, namespace escape, unauthorized manifest/secret, privileged pod and signer misuse        |
| TM-E5   | Self/stale/cross-purpose approval bypasses separation of duties                                            | Explicit incompatible roles, current authorization at action time, purpose/environment binding, expiry/revocation and distinct rollback approval     | Requester self-approval, removed role, PR-to-deploy, deploy-to-rollback, staging-to-prod and concurrent role change      |
| TM-RCV1 | Backup is incomplete, exposed or unusable during ransomware/region loss                                    | Encrypted isolated/immutable backup, separate credentials, PITR, dependency/key inventory and scheduled restore/DR                                   | Corruption/missing segment/revoked key/region loss, tenant/full restore and measured RPO/RTO                             |

## Required security gates

Before exposing untrusted execution:

- Reconcile this model to every authoritative SRS security requirement and obtain independent
  review.
- Pass tenant-isolation tests for SQL, vector, cache, object, workflow, events, audit, telemetry,
  backup and background paths.
- Pass approval-confusion property tests over actor, tenant, run, repository, commit, digest,
  action, environment, scope, expiry, policy and role changes.
- Pass prompt-injection evaluation across source, documentation, tests, issues, encoded/nested
  instructions and retrieval poisoning.
- Pass sandbox escape and secret-canary suites on the actual Firecracker and fallback
  configurations.
- Pass webhook/provider contract, workflow replay/crash/idempotency, artifact
  provenance/signature/admission and supply-chain tampering tests.
- Verify that any failure in authn/authz/tenant/policy/signature/digest/approval evaluation fails
  closed.

Before production acceptance, additionally demonstrate staging canary and separately approved
rollback, backup restoration and measured RPO/RTO, load/chaos behavior, and no unaccepted
critical/high findings.

## Approved security decision baseline

| Area              | Binding direction                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Topology/recovery | AWS/EKS reference with separate production boundary, warm EU DR, certified SLO/capacity/cost/RPO/RTO and scheduled restore/failover exercises (ADR-0002).                                   |
| Tenancy/data      | Shared-control-plane SaaS first plus dedicated installs; tenant scope in every store/path; Public/Internal/Confidential/Restricted; region, retention and encryption controls (ADR-0004).   |
| External AI       | Provider-neutral hosted/local gateway; Restricted content never leaves; configurable organization/repository selection, retention/redaction and offline private deployment (ADR-0003/0004). |
| Sandbox           | Dedicated KVM Firecracker pools in staging/production; rootless only for local/CI/approved trusted workloads; untrusted execution fails closed on missing KVM (ADR-0005).                   |
| Identity/approval | Explicit roles, MFA freshness, separation of duties, two-person production approval, context/digest binding, strict expiry and severity-one break glass (ADR-0005).                         |
| Audit             | Append-only hashes/chains/signed checkpoints/trusted time, offline verification and critical-event WORM replication with seven-year retention (ADR-0005).                                   |
| Gates             | Approved coverage/mutation/retrieval/agent/security-recall thresholds and blocking vulnerability/provenance/image policy (ADR-0005).                                                        |

Actual provider credentials, AWS accounts, dedicated test organizations, signing identities and
production infrastructure are milestone-entry dependencies, not unresolved architecture. Sandbox
egress allowlists, exact secret-injection scopes and incident notification obligations must be
finalized before those features are enabled.

## Implemented local controls as of Phase 0D

- PostgreSQL forced RLS protects the initial organization configuration and audit event stores.
- Transaction-local tenant context is covered by real pooled-connection tests.
- OIDC JWT verification rejects wrong issuer, audience and signing key against configured JWKS.
- Deterministic role policy gates the current protected organization API.
- Tenant-scoped audit events include canonical payload hashes and per-organization hash chaining.
- Database triggers reject audit event update/delete attempts.
- API telemetry emits structured JSON logs with sanitized exception metadata, bounded route labels,
  validated correlation IDs, OpenTelemetry spans and Prometheus request metrics.
- Docker Compose starts digest-pinned PostgreSQL, OPA and OpenTelemetry Collector containers with
  loopback-bound ports and health checks for local development.
- Runtime API and web images are built from digest-pinned bases, pass container HTTP smoke under
  read-only root with dropped capabilities, and run as non-root users.
- Helm/Argo baseline manifests include pod security contexts, disabled service-account token
  automounting, resources, liveness/readiness probes, release-scoped selectors, generated internal
  service URLs, PDB, HPA and default-deny NetworkPolicy with DNS and telemetry allowances, with
  static validation in the local security target.

These controls are local foundation evidence only. Production IdP integration, MFA freshness,
approval/break-glass semantics, WORM replication, API-side OPA enforcement, telemetry dashboards and
retention, Helm rendering, Kubernetes admission, SBOM/signing/scanner gates and sandbox controls
remain unverified.

See `docs/risk-register.md` for prioritization and ownership. This model remains incomplete until
every control and test exists; live Phase 0 platform evidence, later approval, sandbox, deployment
and production-readiness controls remain unverified.
