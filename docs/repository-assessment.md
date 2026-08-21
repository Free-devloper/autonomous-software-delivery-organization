# Repository Assessment

**Assessment date:** 2026-08-19  
**Assessment scope:** current implementation inventory plus historical pre-build baseline  
**Product:** Autonomous Software Delivery Organization

## Current assessment - 2026-08-19

The repository is now a local, uncommitted Git worktree on branch `feature/phase-0-foundation`.
Phase 0A through Phase 0D local foundation work is present: JavaScript/Python workspaces,
Next.js/API health and readiness surfaces, PostgreSQL/Alembic tenancy, forced RLS, configurable OIDC
JWT verification, deterministic role policy, append-only tenant-scoped audit events, structured
telemetry, digest-pinned container builds, Compose infrastructure and static Helm/Argo platform
validation. Current local verification passed with `pnpm verify`, `pnpm test:integration`,
`pnpm dev-infra`, `pnpm deploy:local`, `pnpm smoke:test` and `pnpm test:security`.

The repository still has no commits and no remote GitHub repository/protection evidence, so evidence
is local-file-state evidence rather than immutable commit evidence. Live Helm/kind/EKS rendering and
apply, OPA API integration, production OIDC hardening, SBOM/signing/scanner execution, remote CI and
provider governance remain unverified before final Phase 0 acceptance or Phase 1 entry.

## Initial pre-build snapshot

> This section records the initial inventory. Its missing-decision and missing-SRS statements are
> historical and superseded by the approved decision addendum and the dated update near the end of
> this document.

This is a new, uninitialized repository rather than an existing application. The root contains only
`AGENTS.md`, `project_doc.txt`, and repository-local Codex agent configuration under `.codex/`.
There is no Git repository, source code, test suite, dependency manifest or lockfile, build system,
deployment definition, README, license file, CI configuration, generated artifact, or operational
documentation.

`project_doc.txt` is the only product-requirement source found. It repeatedly refers to an "attached
SRS," but no separate SRS is present. It has no formal requirement identifiers. Accordingly, it is a
provisional requirements source, not a confirmed complete or authoritative SRS. The planning IDs in
`docs/requirements-traceability.md` are internal, non-authoritative identifiers and must be
reconciled with the complete SRS before Phase 0 begins.

No product implementation or verification evidence exists. The repository is therefore at the
pre-Phase-0 planning gate.

## Evidence inspected

| Item                                          | Result                                                                                                                                        |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Applicable instructions                       | Root `AGENTS.md` (148 lines); no nested `AGENTS.md` files                                                                                     |
| Provisional requirements                      | `project_doc.txt` (671 lines)                                                                                                                 |
| Local agent configuration                     | `.codex/config.toml` and five role definitions under `.codex/agents/`                                                                         |
| Root inventory                                | Only `.codex/`, `AGENTS.md`, and `project_doc.txt`                                                                                            |
| Version-control state                         | `git status --short` returned `fatal: not a git repository`                                                                                   |
| Source and tests                              | None found                                                                                                                                    |
| README/contribution/build/deploy/config files | None, apart from `.codex` agent configuration                                                                                                 |
| Dependency state                              | No manifests, lockfiles, virtual environment metadata, or container definitions                                                               |
| Generated artifacts                           | None found                                                                                                                                    |
| Existing user changes                         | Cannot be determined through Git because `.git` is absent; the two root documents and `.codex` files were treated as user-owned and preserved |

The first sandboxed inventory command could not start because `codex-windows-sandbox-setup.exe` was
unavailable. The same read-only inventory was rerun with explicit approval outside that helper and
succeeded. This is an environment/tooling issue, not a repository defect, but it should be resolved
before relying on sandboxed local automation.

## Current capability state

| Area                    | Current state        | Gap to Phase 0                                                           |
| ----------------------- | -------------------- | ------------------------------------------------------------------------ |
| Workspace               | Absent               | Monorepo structure, task runner, language workspaces, lockfiles          |
| Frontend                | Absent               | Next.js/React strict-TypeScript application and UI package               |
| Backend                 | Absent               | FastAPI services, typed contracts, persistence, migrations               |
| Identity/security       | Absent               | OIDC, RBAC, tenant isolation, audit, policy and secrets controls         |
| Workflows/agents        | Absent               | Temporal and LangGraph integration, durable state, typed agent contracts |
| Repository intelligence | Absent               | Provider adapters, immutable Git views, parsing/indexing/retrieval       |
| Sandboxing              | Absent               | Rootless and Firecracker adapters, enforcement and security tests        |
| Verification            | Absent               | Unit through evaluation suites, thresholds, evidence recording           |
| Delivery platform       | Absent               | Containers, Kubernetes, Helm, Argo CD, Terraform, CI/CD                  |
| Operations              | Absent               | Telemetry, dashboards, alerts, backups, recovery and runbooks            |
| Documentation           | Preliminary set only | All implementation and operations documentation remains future work      |

## Requirements-source assessment

The provisional source is detailed enough to plan eight phases and major quality/security
invariants, but not enough to establish a contractually complete traceability baseline because:

- no attached, versioned SRS is present;
- no formal SRS requirement identifiers exist in the available files;
- several project parameters remain bracketed choices;
- measurable targets for scale, SLOs, RPO/RTO, evaluation quality, mutation score, retention, and
  compatibility are absent;
- compliance, residency, model-provider, embedding-provider, cost, and availability expectations are
  unspecified;
- it is unclear whether browser accessibility standards and supported client/platform versions are
  prescribed elsewhere.

The complete SRS and its authoritative version are therefore a hard entry criterion for Phase 0. If
`project_doc.txt` is intended to be the complete SRS, the owner must explicitly say so and approve
the internal planning-ID scheme or provide formal IDs.

## Architecture starting point

Subject to the unresolved decisions, the governing documents direct a provider-neutral monorepo
with:

- `apps/web`, shared TypeScript contracts/configuration/UI packages, and strict public contracts;
- independently deployable Python services for API, workflow, agents, repository access, indexing,
  sandboxing, and evaluation;
- PostgreSQL plus row-level security and pgvector as the transactional and semantic source of truth,
  with Valkey/Redis-compatible caching and S3-compatible artifacts;
- Temporal for durable business workflows and LangGraph for checkpointed agent graphs;
- OIDC, deterministic RBAC/OPA authorization, immutable audit, digest-bound approvals, and
  fail-closed security decisions;
- Kubernetes/Helm/Argo CD delivery with OpenTelemetry, Prometheus, Grafana, Loki, and Tempo;
- sandbox runtime adapters for Firecracker and rootless containers, with strict isolation
  invariants.

This is a direction, not an approved architecture. Material choices are intentionally deferred to
explicit decisions and future ADRs.

## Superseded preliminary gaps and constraints

The list below records the state before the product owner's 2026-08-18 decision addendum. Items 2-9
are superseded by accepted ADR-0001 through ADR-0005; item 1 and the local tooling issue remain
current.

1. **Requirements authority:** no complete, versioned SRS is available.
2. **Platform target:** Kubernetes distribution, primary cloud, regions, and production topology are
   undecided.
3. **Provider scope:** GitHub/GitLab and model/embedding providers are undecided; test organizations
   are not confirmed.
4. **Security/compliance:** classifications, compliance regimes, data residency, retention/deletion,
   audit retention, and incident obligations are absent.
5. **Reliability/capacity:** workload profile, tenancy scale, availability target, latency/error
   SLOs, RPO/RTO, and cost ceiling are absent.
6. **Execution infrastructure:** Firecracker-capable Linux hosts and their operating model are
   unconfirmed.
7. **Quality policy:** mutation threshold, coverage thresholds, security finding policy, and
   evaluation pass criteria are undecided.
8. **Compatibility:** API and data compatibility windows and supported browser/provider/platform
   ranges are undecided.
9. **Repository governance:** Git hosting, branch protection, signing, CODEOWNERS, release policy,
   and license file are absent.
10. **Local tooling:** the Windows sandbox helper failed to launch and needs repair or a documented
    supported alternative.

## Credentials and infrastructure eventually required

None are needed for preliminary planning. Later phases will need, only when their approved tasks
begin:

- an OIDC test realm/client and signing-key rotation test path;
- GitHub and/or GitLab dedicated test organizations with webhook and branch-protection capabilities;
- selected model and embedding test credentials or approved local/offline models;
- Kubernetes clusters, DNS/TLS, container and artifact registries, object storage, secrets service,
  and observability endpoints;
- Firecracker-capable Linux capacity for security and isolation verification;
- staging deployment, backup/restore, chaos, and rollback environments.

Local contract servers and emulators should cover adapter development without live credentials, but
they cannot substitute for required provider and staging evidence.

## Superseded initial gate recommendation

At initial assessment, SRS and architecture decisions were unresolved. They are now resolved by
owner confirmation and the approved decision addendum. Phase 0 still requires explicit build
approval; dependency and image versions must then be researched from official sources, pinned and
recorded before installation or build activity.

## Decision baseline update - 2026-08-18

The product owner subsequently resolved the architecture, platform, provider, tenancy, scale,
SLO/cost/recovery, compliance/residency/retention/classification/encryption, sandbox,
identity/approval, quality/security, compatibility and immutable-audit decisions. The binding
details are recorded in accepted ADR-0001 through ADR-0005 and reflected in the other preliminary
documents.

The intended repository is a new private GitHub monorepo named
`autonomous-software-delivery-organization` under `roytechworkforce`. The reference platform is
cloud-neutral with AWS/EKS in `eu-central-1` and warm DR in `eu-west-1`. GitHub is implemented first
and GitLab is required before final release. Shared-control-plane multi-tenant SaaS is first, with
dedicated-install parity. Provider-neutral hosted/local models, strict classification controls,
Firecracker production isolation, measurable reliability/cost/recovery targets, context-bound human
approvals, WORM-backed audit and explicit quality/security thresholds are approved.

### Remaining Phase 0 gate

Phase 0 local implementation approval was received after the preliminary baseline. The requirements
authority and GitHub organization are resolved; repository creation/protection will still require
authenticated GitHub repository/ruleset permissions. Phase 0D local evidence is present; final Phase
0 acceptance still requires a user decision on the remaining external/live evidence gaps: remote CI,
Helm/kind/EKS rendering and apply, SBOM/signing/scanner execution, provider governance and
immutable-commit binding.
