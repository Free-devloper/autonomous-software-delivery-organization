# ADR-0001: Provider-neutral monorepo direction

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owners:** Product owner and principal engineering owner
- **Requirements source:** `project_doc.txt` sections 2, 3, 5, and 6; root `AGENTS.md`

## Context

The authoritative requirements baseline is `project_doc.txt` plus product-owner decision addendum
version 1.0. It directs a maintainable monorepo, explicit provider adapters, versioned typed
contracts and open-source-first infrastructure. The decision was made before application code
existed; Phase 0A through 0C local foundation work now follows this direction.

## Proposed decision

Use the logical repository layout in `project_doc.txt`, organized around bounded services and shared
contracts. Keep domain rules independent of frameworks and providers. Treat Git hosting, models,
embeddings, object storage, secrets systems, and sandbox runtimes as replaceable adapters behind
versioned typed contracts.

The repository will be a new private monorepo named `autonomous-software-delivery-organization`,
hosted on GitHub under `roytechworkforce`. GitHub is the initial production provider and GitLab
remains required through the same provider-neutral interface. Cloud, tenancy, provider and security
choices are recorded in subsequent accepted ADRs. Concrete package versions remain subject to
official-source compatibility verification before installation.

## Alternatives considered

- **Single deployable modular monolith:** simpler initial operations but conflicts with the
  prescribed independently scalable execution, indexing, workflow, and evaluation concerns unless
  carefully partitioned.
- **Multiple repositories:** increases release and contract coordination before the team has
  evidence that organizational boundaries justify it.
- **Provider-specific architecture:** may shorten a first integration but violates the explicit
  provider-neutral requirement and raises lock-in and testability risk.

## Consequences

- Shared contracts need strict ownership, compatibility checks, and generated client validation.
- Cross-service workflows require idempotency, durable state, observability, and contract testing
  from Phase 0 onward.
- Repository boundaries and deployable boundaries need not be identical; actual service deployment
  topology should be validated by load and failure-mode evidence.
- New provider dependencies require adapter contracts, local contract tests, live-provider
  verification, and compatibility records.

## Security and verification implications

- Authorization, approvals, tenant context, artifact digests, and policy outcomes remain
  deterministic and cannot be delegated to model output.
- Contract and integration suites must prove tenant context and authorization semantics across
  service boundaries.
- A future architecture conformance check should reject direct provider SDK usage outside adapter
  modules.

## Repository governance

Use protected `main`, short-lived feature branches, pull requests for all changes, passing
CI/security checks and two human approvals. Prohibit direct commits and force pushes to protected
branches. Require signed release commits and Dependabot or Renovate. Use Apache-2.0 unless changed
before public release.

This ADR records architecture intent. Phase 0 local implementation approval was later received, but
repository creation/protection, external writes and later phase advancement still require the
separate human gates defined by `AGENTS.md`.
