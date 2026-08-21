# Implementation Plan

**Status:** Active Phase 0 implementation plan; Phase 0A through 0D have local evidence  
**Date:** 2026-08-19  
**Requirements baseline:** authoritative `project_doc.txt` plus approved decision addendum version
1.0

## Delivery policy

Phase 0 local implementation approval is recorded as received in the requirements baseline. Each
later phase still requires the preceding phase's executed exit evidence and explicit approval.
External writes, destructive actions, credentials, production resources and risk acceptance still
require a separate human decision at the relevant gate.

Every milestone begins with a short execution brief naming scope, assumptions, file ownership,
dependencies, risks, and verification commands. It ends with a report of changed
behavior/files/migrations/tests, actual command results, coverage and mutation results, security
findings, limitations, traceability evidence, and the recommended next milestone. A requirement
stays `Planned` until its evidence was executed successfully and linked.

## Dependency map

```text
Authoritative requirements baseline + decisions + build approval
                  |
          Phase 0 foundations
                  |
       Phase 1 repository intelligence
                  |
       Phase 2 requirements/workflows
                  |
       Phase 3 sandboxed generation
                  |
       Phase 4 testing/security
                  |
       Phase 5 review/PR approvals
                  |
       Phase 6 deployment/rollback
                  |
       Phase 7 production readiness
```

Within phases, contracts and security invariants precede user-facing or side-effecting features.
Authentication precedes tenant data APIs; tenant schema and RLS precede tenant features; immutable
artifacts precede approvals; approval semantics precede PR/deploy/rollback side effects; actual
sandbox hardening precedes untrusted execution; observability precedes SLO gates; backup/restore
capability precedes recovery claims.

## Planned repository ownership

| Area                                                                                  | Primary owner                            | Independent verification                           |
| ------------------------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| `apps/web`, `packages/ui`                                                             | Frontend                                 | Testing; reviewer for security-sensitive UI        |
| APIs, domain, data, workflow, agents, repository/indexing/sandbox/evaluation services | Backend specialists split by service     | Testing; reviewer for high-risk paths              |
| `packages/contracts`, cross-service interfaces                                        | Coordinator assigns one owner per change | Consumer contract tests and combined review        |
| Test harnesses and evidence                                                           | Testing                                  | Implementer response; reviewer for high-risk gates |
| Infrastructure and operations                                                         | Backend/platform owner                   | Testing and reviewer                               |
| Planning, ADRs, traceability, risks                                                   | Coordinator                              | User at phase gates; reviewer as warranted         |

One owner edits a file at a time. Dependent or overlapping changes are serialized; independent UI,
service, infrastructure, and test work may run in parallel only after contracts are agreed.

## Milestones

| Milestone                                 | Scope and planned paths                                                                                                  | Entry criteria                                        | Exit evidence                                                                                            | Dependencies / principal risks                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 0A Workspace and contracts                | Root workspace, `apps/`, `services/`, `packages/contracts`, config validation, license, lockfiles, task surface          | Phase 0 approval; runtime/version selections recorded | Bootstrap, format, lint, strict TS/Python typecheck and unit harness execute reproducibly                | SRS and compatibility decisions; supply-chain risk       |
| 0B Persistence and tenancy                | PostgreSQL/Alembic, tenant model, RLS, migration discipline                                                              | 0A contracts/config                                   | Migration round-trip/compatibility and cross-tenant database tests pass                                  | Tenant model, residency, retention, admin boundary       |
| 0C Identity, RBAC and audit               | OIDC, roles, deterministic policy, immutable audit                                                                       | 0B; IdP/role decisions                                | Auth negative tests, privilege matrix, fail-closed policy, audit tamper tests                            | Claim model, SoD, audit retention                        |
| 0D Delivery and telemetry foundation      | CI, secret/security checks, local environment, containers, OTel, Kubernetes/Helm baseline                                | 0A–0C stable                                          | Documented local start, CI gate set, telemetry assertions, Helm/Kubernetes validation and smoke evidence | Target cluster/cloud, image policy, tooling availability |
| 1A SCM contracts                          | GitHub/GitLab adapters, registration, immutable commit resolution                                                        | Phase 0 exit approval; provider scope                 | Contract-server tests plus dedicated test-org evidence when available                                    | Provider permissions/test organizations                  |
| 1B Repository views                       | Mirrors, isolated worktrees, browser/source/lexical search                                                               | 1A immutable identity                                 | Commit-isolation, cleanup, API, browser and accessibility evidence                                       | Untrusted paths, storage/capacity                        |
| 1C Structural indexing                    | tree-sitter, LSP symbols/definitions/references                                                                          | 1B                                                    | Parser corpus/property tests and language fixtures                                                       | Supported languages/tool versions                        |
| 1D Semantic retrieval                     | Commit-scoped chunks, embeddings, pgvector hybrid search, freshness                                                      | 1C; provider/data policy                              | No cross-commit/tenant mixing; retrieval and freshness thresholds pass                                   | Embedding privacy, missing evaluation thresholds         |
| 2A Requirement domain                     | Immutable revisions, acceptance criteria, clarifications, trace links                                                    | Phase 1 approval                                      | Domain/property/database/API/browser evidence                                                            | Authoritative requirement model                          |
| 2B Planning agents                        | Typed analyst/architect agents, evidence-backed plans, work packages, budgets                                            | 2A; model policy                                      | Contract/evaluation/prompt-injection tests and evidence linkage pass                                     | Model/embedding providers and quality thresholds         |
| 2C Durable lifecycle                      | Temporal lifecycle, persisted LangGraph, pause/resume/cancel/retry, plan approval                                        | 2A–2B                                                 | Replay/crash/idempotency/approval-wait tests; waits consume no model resources                           | State-versioning and approval semantics                  |
| 2D Live execution UX                      | Authorized event stream and graph                                                                                        | 2C event contract                                     | Reconnect/order/access-control/browser/a11y evidence                                                     | Backpressure and leakage                                 |
| 3A Sandbox contract and profiles          | Controller, rootless profile, Firecracker adapter, limits and policies                                                   | Phase 2 approval; runtime decision/infrastructure     | Adapter tests on actual profiles; hardening assertions                                                   | Firecracker capacity; fallback risk                      |
| 3B Filesystem/network/secrets enforcement | Scoped worktrees, descriptor-safe paths, default-deny egress, ephemeral secrets                                          | 3A                                                    | Traversal/symlink/network/socket/mount/secret-canary regression suite passes                             | Sandbox escape and credential exfiltration               |
| 3C Patch pipeline                         | Coding agent, canonical patch/digest/store/integration/conflicts                                                         | 3B                                                    | Digest reproducibility, deterministic multi-package integration, replay/idempotency tests                | Untrusted model output and artifact integrity            |
| 3D Diff review UI                         | Monaco diff viewer and safe source rendering                                                                             | 3C contracts                                          | Browser, accessibility and XSS fixtures pass                                                             | Rendering untrusted content                              |
| 4A Test intelligence                      | Discovery and unit/integration/browser generation; baseline/patched attribution                                          | Phase 3 approval                                      | Generated tests execute meaningful behavior; attribution tests pass                                      | Generated-test quality                                   |
| 4B Quality measurement                    | Coverage, mutation and flake analysis                                                                                    | 4A; approved thresholds                               | Changed-line/branch and mutation thresholds; deterministic flake reports                                 | Unset thresholds and runtime cost                        |
| 4C Security pipeline                      | SAST/dependency/secret/container/IaC tools, SBOM/SARIF, dedupe/triage                                                    | 4A; severity policy                                   | Known-vulnerable fixture detection, normalized evidence and blocking behavior                            | Scanner availability/licensing, false positives          |
| 4D Adversarial agents                     | Prompt-injection controls, security/test agents, test-weakening detection                                                | 4A–4C                                                 | Injection corpus cannot alter policy; weakening/deletion is blocked                                      | Evaluation recall thresholds                             |
| 5A Review domain and UI                   | Reviewer agent, dashboard, inline/threaded comments                                                                      | Phase 4 approval                                      | API/agent/browser/a11y evidence                                                                          | Untrusted content and model-review limitations           |
| 5B Approval integrity                     | Context/digest-bound approval, expiry, staleness, SoD                                                                    | 5A; approved role policy                              | Property/concurrency tests reject self/stale/replayed/cross-context approvals                            | Critical authorization risk                              |
| 5C PR side effects                        | Idempotent provider PR adapters, webhooks, sync and reconciliation                                                       | 5B                                                    | Valid approval required; duplicate request creates one PR; spoof/replay tests; live test-org evidence    | External permissions and provider drift                  |
| 6A Release planning                       | Release agent, versioned plan, migration/compatibility analysis                                                          | Phase 5 approval                                      | Schema/compatibility/migration-plan evidence                                                             | Compatibility window and data-loss risk                  |
| 6B Delivery strategies                    | Immutable signed artifacts, Argo CD, rolling/canary/blue-green and SLO gates                                             | 6A; staging/registry/signing access                   | Signature/admission tests and staging canary evidence                                                    | Cluster/cloud topology and supply chain                  |
| 6C Separate rollback                      | Purpose-bound deployment/rollback approvals, rollback and post-check                                                     | 6B; rollback policy                                   | Approval-confusion suite and separately approved staging rollback rehearsal                              | Irreversible database changes                            |
| 7A Evaluation suite                       | Correctness, accepted change, regression, security recall, test quality, mutation, traceability and recovery evaluations | Phase 6 approval; approved thresholds/datasets        | Versioned reports meet thresholds                                                                        | Dataset representativeness                               |
| 7B Capacity and cost                      | Load/performance, token/cost/latency dashboards, quotas                                                                  | 7A; scale/SLO/cost targets                            | Target-load SLO report and dashboard checks                                                              | Provider quotas/cost/noisy neighbors                     |
| 7C Resilience and operations              | Chaos, backup/restore, DR and runbooks                                                                                   | 7B; RPO/RTO/topology                                  | Measured restore/DR and failure-injection evidence                                                       | Backup completeness/key/region dependency                |
| 7D Staging acceptance                     | Complete requirement-to-PR, deploy and distinct rollback flow                                                            | 7A–7C                                                 | All mandatory rows link passing evidence; no unaccepted critical/high security issues                    | All preceding risks and approvals                        |

## Proposed milestone verification commands

These are exact task-runner contracts. Phase 0A through 0C commands now exist where listed in the
README or phase reports; later milestone commands remain planned and intentionally fail nonzero
until their owning milestone is implemented. Each command must fail nonzero when its evidence is
incomplete.

| Milestone | Exact proposed commands                                                                                                                                        |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0A        | `make bootstrap`<br>`make format`<br>`make lint`<br>`make typecheck`<br>`make TEST_SCOPE=workspace test-unit`                                                  |
| 0B        | `make TEST_SCOPE=database test-integration`<br>`make TEST_SCOPE=tenant-isolation test-security`                                                                |
| 0C        | `make TEST_SCOPE=identity-policy-audit test-unit`<br>`make TEST_SCOPE=identity-policy-audit test-integration`<br>`make TEST_SCOPE=approval-auth test-security` |
| 0D        | `make dev-infra`<br>`make TEST_SCOPE=telemetry test-integration`<br>`make TEST_SCOPE=platform test-security`<br>`make deploy-local`<br>`make smoke-test`       |
| 1A        | `make TEST_SCOPE=scm-contracts test-contract`<br>`make TEST_SCOPE=scm-live test-integration`                                                                   |
| 1B        | `make TEST_SCOPE=repository-views test-integration`<br>`make TEST_SCOPE=repository-browser test-e2e`<br>`make TEST_SCOPE=repository-boundaries test-security`  |
| 1C        | `make TEST_SCOPE=structural-index test-unit`<br>`make TEST_SCOPE=structural-index test-integration`<br>`make TEST_SCOPE=parser-corpus test-security`           |
| 1D        | `make TEST_SCOPE=hybrid-retrieval test-integration`<br>`make TEST_SCOPE=retrieval test-evaluation`<br>`make TEST_SCOPE=index-isolation test-security`          |
| 2A        | `make TEST_SCOPE=requirements test-unit`<br>`make TEST_SCOPE=requirements test-integration`<br>`make TEST_SCOPE=requirements test-e2e`                         |
| 2B        | `make TEST_SCOPE=planning-agents test-contract`<br>`make TEST_SCOPE=planning-agents test-evaluation`<br>`make TEST_SCOPE=agent-policy test-security`           |
| 2C        | `make TEST_SCOPE=workflow-replay test-integration`<br>`make TEST_SCOPE=workflow-failures test-resilience`<br>`make TEST_SCOPE=plan-approval test-security`     |
| 2D        | `make TEST_SCOPE=live-events test-integration`<br>`make TEST_SCOPE=execution-graph test-e2e`<br>`make TEST_SCOPE=event-isolation test-security`                |
| 3A        | `make TEST_SCOPE=sandbox-adapters test-contract`<br>`make TEST_SCOPE=sandbox-profiles test-security`                                                           |
| 3B        | `make TEST_SCOPE=sandbox-boundaries test-security`<br>`make TEST_SCOPE=sandbox-failures test-resilience`                                                       |
| 3C        | `make TEST_SCOPE=patch-pipeline test-integration`<br>`make TEST_SCOPE=patch-properties test-unit`<br>`make TEST_SCOPE=artifact-integrity test-security`        |
| 3D        | `make TEST_SCOPE=diff-viewer test-unit`<br>`make TEST_SCOPE=diff-viewer test-e2e`<br>`make TEST_SCOPE=untrusted-rendering test-security`                       |
| 4A        | `make TEST_SCOPE=test-intelligence test-integration`<br>`make TEST_SCOPE=generated-tests test-evaluation`                                                      |
| 4B        | `make TEST_SCOPE=quality-measurement test-integration`<br>`make test-mutation`<br>`make TEST_SCOPE=flake-detection test-resilience`                            |
| 4C        | `make TEST_SCOPE=security-pipeline test-integration`<br>`make test-security`<br>`make TEST_SCOPE=security-tools test-contract`                                 |
| 4D        | `make TEST_SCOPE=adversarial-agents test-evaluation`<br>`make TEST_SCOPE=prompt-injection test-security`<br>`make TEST_SCOPE=test-weakening test-security`     |
| 5A        | `make TEST_SCOPE=review test-integration`<br>`make TEST_SCOPE=review-dashboard test-e2e`<br>`make TEST_SCOPE=review-agent test-evaluation`                     |
| 5B        | `make TEST_SCOPE=approval-properties test-security`<br>`make TEST_SCOPE=approval-concurrency test-integration`                                                 |
| 5C        | `make TEST_SCOPE=pr-providers test-contract`<br>`make TEST_SCOPE=pr-side-effects test-integration`<br>`make TEST_SCOPE=webhooks test-security`                 |
| 6A        | `make TEST_SCOPE=release-plans test-contract`<br>`make TEST_SCOPE=release-compatibility test-integration`                                                      |
| 6B        | `make build`<br>`make TEST_SCOPE=supply-chain test-security`<br>`make TEST_SCOPE=rollout test-integration`<br>`make deploy-local`<br>`make smoke-test`         |
| 6C        | `make TEST_SCOPE=rollback-approval test-security`<br>`make rollback`<br>`make smoke-test`                                                                      |
| 7A        | `make test-evaluation`<br>`make TEST_SCOPE=requirement-evidence verify`                                                                                        |
| 7B        | `make TEST_SCOPE=target-load test-performance`<br>`make TEST_SCOPE=cost-latency test-evaluation`                                                               |
| 7C        | `make backup`<br>`make restore`<br>`make TEST_SCOPE=chaos-recovery test-resilience`<br>`make smoke-test`                                                       |
| 7D        | `make verify`<br>`make TEST_SCOPE=full-workflow test-e2e`<br>`make TEST_SCOPE=production-readiness test-security`<br>`make TEST_SCOPE=staging test-resilience` |

## Phase gates and proposed verification surface

The final task runner may be a Makefile or documented equivalent. The required command surface is
`bootstrap`, `dev-infra`, `dev`, `format`, `lint`, `typecheck`, `test`, `test-unit`,
`test-integration`, `test-e2e`, `test-security`, `test-mutation`, `verify`, `build`, `deploy-local`,
`smoke-test`, `backup`, `restore`, and `rollback`.

| Phase | Mandatory executed exit evidence before requesting next approval                                                                                                                  |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Documented development start; unit/integration harness; cross-tenant RLS tests; CI format/lint/type/test/security gates; clean secret scan; local and Kubernetes foundation smoke |
| 1     | Dedicated real repository connection; browse/search; immutable commit isolation; indexing/retrieval/freshness evaluation thresholds                                               |
| 2     | Requirement-to-structured-plan flow with repository evidence; durable interruption/recovery; zero model use while awaiting approval; authorized live events                       |
| 3     | Actual isolation profile; out-of-scope/path/network escape rejection; secret containment; reproducible patch digest; deterministic integration; sandbox regressions               |
| 4     | Baseline versus patched evidence; meaningful generated tests; coverage/mutation/flake reports; reproducible normalized security findings; injection and test-weakening gates      |
| 5     | Exact-artifact/SoD/expiry/replay property tests; one idempotent PR; validated webhooks; provider checks remain authoritative                                                      |
| 6     | Purpose-separated approvals; immutable signed deployment; staging canary and separately approved rollback; post-rollback checks; database limitations stated                      |
| 7     | Evaluation thresholds; target-load SLOs; cost visibility; chaos/recovery; observed RPO/RTO; full staging workflow; traceability completeness                                      |

Evidence must record the requirement/test ID, exact command, tool and image versions/digests,
environment, fixture/seed, result, artifact URL or digest, and timestamp. External boundaries may
use local contract servers during development, but provider support is not complete until the
required dedicated-organization or staging evidence exists.

## Phase 0 decision status

| Area                                                                              | Status                                                                                                             | Decision record                                                    |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Repository/monorepo/governance                                                    | Resolved: GitHub organization `roytechworkforce`                                                                   | ADR-0001                                                           |
| Cloud, environments, capacity, SLO, cost and DR                                   | Resolved                                                                                                           | ADR-0002                                                           |
| Git/model/embedding providers and compatibility                                   | Resolved                                                                                                           | ADR-0003                                                           |
| Tenancy, compliance, residency, retention, classification and encryption          | Resolved                                                                                                           | ADR-0004                                                           |
| Firecracker, roles, approvals, break glass, audit and quality/security thresholds | Resolved                                                                                                           | ADR-0005                                                           |
| Authoritative requirements                                                        | Resolved: `project_doc.txt` is the only complete project document; decision addendum v1.0 supplements it           | Owner confirmation                                                 |
| Phase 0 implementation authorization                                              | Received for local Phase 0 implementation; does not authorize external writes                                      | Requirements baseline and decision addendum                        |
| Phase 0A workspace/contracts                                                      | Verified locally                                                                                                   | `pnpm verify` evidence                                             |
| Phase 0B persistence/tenancy                                                      | Verified locally for relational PostgreSQL scope                                                                   | `pnpm verify`; `pnpm test:integration`                             |
| Phase 0C identity/RBAC/audit                                                      | Verified locally for OIDC JWT, deterministic policy and PostgreSQL audit scope                                     | `docs/phase-0c-identity-rbac-audit.md`                             |
| Phase 0D delivery/telemetry/Kubernetes                                            | Verified locally for telemetry, local images, Compose infrastructure, static Helm/Argo validation and smoke checks | `docs/phase-0d-delivery-telemetry-platform.md`                     |
| Phase 1 approval eligibility                                                      | Not yet eligible for live/provider claims                                                                          | Requires user decision on remaining Phase 0 external evidence gaps |

The exact product-owner constraints and verification mappings are versioned in
`docs/decision-addendum-2026-08-18.md`; ADR-0001 through ADR-0005 define their architectural
consequences.

Provider credentials, dedicated test organizations, AWS accounts, clusters, registries, signing
identities and scanner databases are required only when their approved milestones begin. Local
contract servers remain mandatory when live credentials are unavailable, but cannot satisfy final
live verification.

## Current validation status

The repository now contains local Phase 0A through 0D implementation and evidence. Current local
commands executed successfully on 2026-08-19: `pnpm verify`, `pnpm test:integration`,
`pnpm dev-infra`, `pnpm deploy:local`, `pnpm smoke:test` and `pnpm test:security`. Phase 0D evidence
includes Docker image builds, OpenTelemetry/Prometheus assertions, Compose OPA/collector health and
static Kubernetes/Helm validation. The GitHub repository has no commits and no remote
provider-rule/CI evidence yet, Helm/kind tooling was unavailable in the current environment, and
SBOM/signing/scanner evidence remains unverified, so Phase 1 should not start until the user decides
whether local Phase 0 evidence is sufficient for the next gate or provides the missing live
infrastructure approvals.
