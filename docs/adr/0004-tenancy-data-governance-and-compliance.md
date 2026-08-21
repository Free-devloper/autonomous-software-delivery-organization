# ADR-0004: Tenancy, data governance and compliance control baseline

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owner:** Product owner

## Decision

Support multi-tenant SaaS and dedicated single-tenant installations from the same application code
and Helm charts. Implement a shared-control-plane multi-tenant SaaS first. Every tenant record
carries organization identity; PostgreSQL RLS, object paths/encryption contexts, cache keys,
vectors, events, logs and metrics are tenant scoped. High-security customers can use isolated
cluster, database and account deployments.

Design evidence and controls for SOC 2 Type II, ISO 27001, GDPR, CCPA/CPRA, OWASP ASVS Level 2, NIST
SSDF and SLSA-compatible provenance without claiming certification before authorized audit.

Organizations select an approved data region. Source, embeddings, artifacts, database and backups
remain in-region unless explicitly authorized. Cross-region telemetry is aggregated and stripped of
source, prompts, secrets and personal data. Dedicated deployments support customer-controlled
residency.

Classifications are Public, Internal, Confidential and Restricted. Restricted content never reaches
external models, is stored only in approved encrypted stores, requires explicit roles and fresh
authentication, and every access is audited. Secrets/private keys never enter prompts.

Use TLS 1.3 where supported with TLS 1.2 minimum, AES-256-equivalent at rest, envelope encryption
through cloud KMS/OpenBao, separate production/non-production keys, optional tenant keys and
automated credential/key rotation without contract changes.

## Retention baseline

Requirements/plans/traceability: 3 years; runs: 1 year; sandbox logs: 90 days; prompts/responses: 30
days default; security findings: 3 years after closure; approvals/deployments and immutable audit: 7
years; temporary worktrees/sandboxes: delete within 24 hours; unreferenced intermediates: 30 days.
Backups retain 35 daily, 12 monthly and 7 annual recovery points. Legal holds override expiry.

## Consequences and verification

Classification, residency, retention, encryption and tenant policy apply across every store,
provider, workflow, telemetry and backup path. Cross-tenant, region-egress,
retention/deletion/legal-hold, key-rotation and restricted-data tests are mandatory. These controls
support audits but do not constitute certification.
