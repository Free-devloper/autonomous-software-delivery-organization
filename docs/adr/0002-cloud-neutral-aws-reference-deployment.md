# ADR-0002: Cloud-neutral AWS reference deployment

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owner:** Product owner

## Decision

Keep application, infrastructure and provider contracts cloud-neutral while certifying AWS as the
primary reference deployment: EKS in `eu-central-1`, warm DR in `eu-west-1`, ECR, S3, Route 53,
CloudFront/AWS WAF, AWS KMS, and OpenBao or AWS Secrets Manager behind a provider-neutral interface.
Use OpenTofu or Terraform-compatible modules, Helm and Argo CD. Production artifacts are immutable
image digests.

Environments are `local` (Docker Compose and kind), `ci` (ephemeral namespace per pull request),
shared `development`, production-equivalent `staging`, isolated customer-facing `production`, and
warm `dr`. Use separate accounts where practical; production has a separate cluster/database and
never shares credentials with non-production.

## Certified capacity and service levels

Plan for 1,000 organizations, 10,000 repositories, 500 concurrent agent runs, 2,000 scheduled
sandboxes, 10,000 web sessions, repositories up to 20 GB/5 million source lines, 100 million chunks
and 50,000 durable events/second.

Targets: control plane 99.9%; approval/audit reads 99.95%; read API p95 <400 ms; write API p95 <800
ms excluding external work; events p95 <2 s; search p95 <1.5 s; interrupted recovery >=99%;
privileged trace completeness >=95%; privileged audit capture 100%.

Budgets are configurable per organization/run, warn at 75%, stop at 100%, estimate before run and
keep unaccounted spend below 5%. Cache reuse requires matching tenant, authorization, model version
and content digest.

RPO/RTO: database 5 min/60 min; acknowledged audit/approvals target zero RPO; artifacts 15 min RPO;
regional RTO 4 h; Git configuration zero RPO. Provide cross-region encrypted replication, PITR,
quarterly restores, semiannual regional failover and annual full DR exercise.

## Consequences and verification

Capacity, latency, availability, cost, recovery and environment isolation become release gates.
AWS-specific implementations remain adapters/modules and cannot leak into domain contracts. Exact
service/image versions and digests require official-source verification. This ADR does not authorize
cloud resource creation.
