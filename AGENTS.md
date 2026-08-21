# Autonomous Software Delivery Organization - Agent Instructions

These instructions apply to the entire repository. `project_doc.txt` and the complete SRS are the
governing product requirements. If an instruction conflicts with a direct user instruction, stop and
ask the user which requirement governs.

## Mission and quality bar

Build the Autonomous Software Delivery Organization as production-quality, runnable software. Do not
substitute prototypes, static mockups, placeholder APIs, pseudocode, empty scaffolding, hardcoded
demonstration data, or mock-only tests for required behavior.

The completed repository must include application code, real automated verification, security
controls, infrastructure definitions, local and production-style deployment instructions, rollback
and recovery procedures, operational documentation, an SBOM, and traceable evidence for every
mandatory SRS requirement.

Use open-source-first, provider-neutral designs. Never invent package versions. Inspect current
stable releases before selecting dependencies, pin compatible application dependencies with
lockfiles, pin production images by digest, and record selections in `docs/compatibility-matrix.md`.

## Human approval gate

- Do not start feature implementation, install dependencies, run a build, deploy, create external
  resources, or make external writes until the user has reviewed the preliminary deliverables and
  explicitly approved starting the build.
- Repository inspection and creation of the preliminary planning documents are allowed before build
  approval.
- Before requesting build approval, present the repository assessment, traceability matrix,
  milestone plan, risk register, threat-model outline, proposed compatibility matrix, assumptions,
  and all consequential open questions.
- During the build, ask whenever a missing decision could materially affect product behavior,
  architecture, security, compliance, cost, provider choice, deployment, compatibility, or data
  handling. Ask for credentials or permissions only when the next approved task needs them.
- Stop for destructive actions, external writes not already approved, security or compliance risk
  acceptance, required credentials, and human approval gates defined by the SRS.
- At every phase boundary, report the exit evidence and obtain explicit approval before advancing to
  the next phase.

## Project decisions that must be resolved or explicitly assumed

Before Phase 0 implementation, determine and document:

- Whether this is a new or existing repository.
- Deployment target: local Kubernetes, AWS EKS, GCP GKE, Azure AKS, or another target.
- Source-control provider: GitHub, GitLab, or both.
- Primary cloud: AWS, GCP, Azure, or cloud-neutral.
- The location and authoritative version of the complete SRS.
- Required model providers, embedding providers, and offline/local-model expectations.
- Initial scale, availability/SLO, RPO/RTO, data residency, retention, and compliance requirements.
- Whether Firecracker-capable Linux infrastructure and provider test organizations are available.
- The agreed mutation-testing threshold and compatibility window.

Defaults, unless the repository or SRS says otherwise, are development/staging/production
environments, Keycloak-compatible OIDC, pnpm for TypeScript, uv for Python, Apache-2.0 licensing,
configurable provider-neutral model access, and private engineering repositories as the target use
case. Never silently assume a choice that materially changes the architecture.

## Project agent team

The primary agent is the entry point and routes work to the smallest useful set of specialists.

- `frontend`: Owns `apps/web` and `packages/ui`, including accessibility, responsive behavior,
  browser state, Monaco integration, TanStack Query, live events, component tests, and Playwright
  coverage.
- `backend`: Owns APIs, domain services, persistence, migrations, tenant isolation, authorization,
  workflows, agent services, repository intelligence, sandbox control, integrations, telemetry, and
  server-side performance.
- `testing`: Owns test strategy, real-behavior automated tests, reproduction cases, security and
  resilience tests, evaluation thresholds, coverage/mutation evidence, and verification reporting.
- `reviewer`: Performs read-only review for correctness, security, tenant isolation, authorization,
  approval integrity, regressions, public compatibility, maintainability, and missing evidence. The
  reviewer never edits files.
- `coordinator`: Owns cross-cutting decomposition, phase planning, bounded assignments, handoffs,
  combined-diff inspection, traceability updates, risk tracking, integration verification, and the
  concise final report.

### Routing rules

- Delegate narrowly scoped client work to `frontend`, server/data/platform work to `backend`,
  verification work to `testing`, and independent final review to `reviewer`.
- Delegate multi-area milestones to `coordinator`, which may dispatch relevant specialists.
- Use multiple agents only for genuinely independent workstreams. Serialize work that touches the
  same files or depends on unfinished output.
- Give every delegated task explicit scope, owned files, constraints, expected output, security
  considerations, and validation criteria.
- One agent owns a file at a time. Agents share the worktree, must preserve unrelated user edits,
  and must not revert another agent's changes.
- High-risk changes involving authentication, authorization, tenant isolation, approvals, policy,
  sandboxing, secrets, migrations, artifact integrity, public APIs, or data loss require testing and
  read-only reviewer sign-off.

## Mandatory work before implementation

Before requesting authorization to build:

1. Read the complete SRS, `project_doc.txt`, every applicable `AGENTS.md`, and repository README,
   contribution, build, deployment, and configuration files.
2. Inspect the full repository, existing code and tests, conventions, generated artifacts,
   dependency state, and uncommitted changes.
3. Identify requirement gaps, architectural risks, unresolved decisions, and work that requires
   credentials or infrastructure.
4. Create and present:
   - `docs/repository-assessment.md`
   - `docs/implementation-plan.md`
   - `docs/requirements-traceability.md`
   - `docs/risk-register.md`
   - `docs/compatibility-matrix.md`
   - `docs/threat-model.md`
   - `docs/adr/`
5. Divide delivery into independently testable milestones with entry criteria, exit criteria,
   dependencies, risks, and verification commands.
6. Map every SRS requirement identifier to its planned component, milestone, source files, tests,
   current status, and verification evidence.
7. Present the consequential questions and receive explicit user approval before beginning Phase 0
   implementation.

A requirement is complete only when its acceptance evidence has been executed successfully and
recorded. The existence of code is not completion evidence.

## Architecture and repository direction

Prefer a maintainable monorepo unless the existing repository provides a justified alternative. The
expected logical layout is:

- `apps/web`
- `services/api`, `services/workflow`, `services/agents`, `services/repository`, `services/indexer`,
  `services/sandbox`, and `services/evaluation`
- `packages/contracts`, `packages/config`, and `packages/ui`
- `infra/helm`, `infra/argocd`, and `infra/terraform`
- `tests/unit`, `tests/contract`, `tests/integration`, `tests/e2e`, `tests/security`,
  `tests/resilience`, `tests/performance`, and `tests/evaluation`
- `docs/adr` and `docs/runbooks`

Document material layout deviations in an ADR.

Use the technology baseline from `project_doc.txt`: Next.js/React/strict
TypeScript/Monaco/Tailwind/TanStack Query; FastAPI/Pydantic/SQLAlchemy/Alembic/OpenAPI 3.1/RFC 9457
errors; LangGraph plus Temporal; PostgreSQL with row-level security and pgvector; Valkey or
Redis-compatible caching; S3-compatible storage; tree-sitter, LSP, ripgrep, and hybrid search;
Kubernetes, Helm, Argo CD, OpenTelemetry, Prometheus, Grafana, Loki, and Tempo; OPA policy;
OpenBao/Vault-compatible secrets; and the specified open-source security toolchain.

All provider integrations - including GitHub, GitLab, models, embeddings, object storage, secrets,
and sandbox runtimes - must use explicit adapter interfaces and versioned typed contracts.

## Delivery phases

Complete and verify one phase before requesting approval to advance:

0. Engineering foundations: workspace, reproducible development, CI/quality gates, configuration,
   persistence/migrations, OIDC, tenant isolation, RBAC, immutable audit, telemetry, local
   development, Kubernetes, and Helm.
1. Repository intelligence: provider adapters, immutable commit resolution, mirrors/worktrees,
   browsing/search, parsing, symbols, semantic chunks, pgvector hybrid retrieval, and freshness.
2. Requirements and planning: revisions, acceptance criteria, clarification, traceability,
   analyst/architect agents, work packages, budgets, durable Temporal lifecycle, persisted LangGraph
   state, interrupts, and live events.
3. Sandboxed code generation: sandbox controller, rootless and Firecracker adapters, deny-by-default
   networking, limits, secret injection, scoped worktrees, path enforcement, coding agent,
   content-addressed patches, deterministic integration, conflict detection, and diff UI.
4. Testing and security: test generation/discovery, mutation and coverage analysis, flake detection,
   SAST/dependency/secret/container/IaC scans, SBOM/SARIF, prompt-injection defenses, and
   security/test agents.
5. Review and pull requests: review UI, threaded comments, digest-bound approvals, separation of
   duties, expiry/staleness controls, idempotent GitHub/GitLab PR adapters, webhook validation, and
   reconciliation.
6. Deployment and rollback: release plans, migrations and compatibility, rollout strategies, Argo
   CD, immutable artifacts, separate deployment/rollback approvals, SLO gates, and post-rollback
   verification.
7. Evaluation and production readiness: quality/security/recovery evaluations, cost/latency
   dashboards, load and chaos tests, backup/restore, disaster recovery, runbooks, and complete
   staging proof.

The detailed phase scope and exit criteria in `project_doc.txt` remain mandatory; this summary does
not replace them.

## Engineering and security invariants

- Keep TypeScript strict and Python fully type-checked. Public boundaries require clear, versioned
  contracts.
- Separate domain rules from frameworks and providers. Authorization, approvals, state transitions,
  and policy decisions must be deterministic code; model output can never authorize an action.
- Treat repository content, prompts, webhooks, generated patches, and artifacts as untrusted input.
- Enforce tenant isolation with PostgreSQL row-level security and verify it with cross-tenant tests.
- Bind approvals to immutable artifact digests, run/repository/action/environment context, actor,
  scope, and expiry. Invalidate stale approvals and enforce separation of duties.
- Make side effects idempotent and long-running work resumable. Use durable checkpoints and ensure
  approval waits consume no model resources.
- Never log or persist secrets in prompts, patches, snapshots, artifacts, or telemetry.
- Use versioned migrations and expand-migrate-contract for production schema evolution.
- Preserve documented API compatibility windows.
- Emit structured logs with correlation IDs, OpenTelemetry traces, and Prometheus metrics from every
  service.
- Execute untrusted repositories without a host Docker socket or unrestricted host mounts. Use
  non-root users, read-only root filesystems, dropped capabilities, seccomp/AppArmor, default-deny
  networks, and strict time/resource limits.
- Fail closed when authorization, policy, signature, digest, approval, or tenant verification cannot
  be completed.
- Do not suppress quality/security failures, weaken or delete tests to pass, add TODO placeholders
  for mandatory work, or use mutable production image tags.

## Verification requirements

For each milestone, add and run the applicable unit, property, contract, database, tenant-isolation,
integration, browser, accessibility, mutation, security, adapter, workflow-replay, idempotency,
approval-confusion, prompt-injection, sandbox-escape, failure-injection, resilience, and performance
tests.

Tests must execute meaningful behavior. Mock external boundaries where needed, but verify adapters
against contract servers or dedicated test organizations. Every defect fix requires a regression
test. Never report a test as passing unless it was actually executed and its successful output
observed.

Security coverage must include cross-tenant access, privilege escalation, stale/self/replayed
approvals, digest substitution, webhook spoofing/replay, repository-content prompt injection, path
traversal/symlinks, malicious installation, sandbox network escape, secret leakage, log injection,
XSS, SSRF, command injection, unsafe deserialization, artifact tampering, dependency confusion, and
unsigned or compromised images.

## Deployment and operational deliverables

Provide verified local and production-style Kubernetes deployments. Expose the required workflows
through a Makefile, Taskfile, or documented equivalent: bootstrap, development infrastructure,
development server, format, lint, typecheck, unit/integration/e2e/security/mutation tests, full
verification, build, local deploy, smoke test, backup, restore, and rollback.

Include safe example configuration, containerized local development, Helm/Kubernetes and Argo CD
definitions, infrastructure modules, network and pod security, resource limits, autoscaling,
disruption budgets, migrations, backup/restore jobs, observability dashboards and alerts, and
synthetic smoke tests.

Maintain all documentation required by `project_doc.txt`, including setup, architecture, API and
agent guides, security and threat model, data model,
deployment/Kubernetes/migration/rollback/backup/DR guides, troubleshooting,
user/admin/provider/evaluation/cost guides, incident runbooks, ADRs, compatibility and traceability
matrices, limitations, and release notes. Documentation commands must be executed and verified.

## Progress, blockers, and handoff

At the start of each approved milestone, report scope, assumptions, expected files, risks,
dependencies, and verification plan. At its end, report functionality, changed files, migrations,
tests, commands and results, coverage/mutation results, security findings, limitations, traceability
updates, and the recommended next milestone.

When blocked, show the exact failed command or operation, explain the known root cause, attempt safe
in-scope remediation, and ask only for the consequential decision, permission, credential, or risk
acceptance needed. Missing live credentials should not block local contract-server implementations
and unrelated approved work.

The system is complete only when all mandatory SRS requirements have passing traceable evidence,
local and staging workflows succeed, security/tenant/approval gates pass, deployment and separately
approved rollback are demonstrated, operational controls are verified, required documentation is
complete, and no mandatory behavior remains placeholder or mock-only.
