# ADR-0005: Sandbox, approval, audit and quality gates

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owner:** Product owner

## Sandbox decision

Use Firecracker on dedicated KVM-capable Linux sandbox node pools in staging/production. Taint
nodes; require explicit tolerations; keep control-plane workloads away; restrict network/security
groups; use ephemeral disks; destroy microVMs/worktrees after completion; attest
Firecracker/kernel/rootfs digest and policy. Rootless containers are limited to local, CI and
approved trusted repositories. Untrusted public production work fails closed when KVM is
unavailable.

## Identity and approval decision

Roles: organization owner, organization administrator, repository administrator, requester,
repository maintainer, security reviewer, release manager, run operator, auditor, billing
administrator, read-only viewer and service account.

Agents never approve. Requesters cannot self-approve production deployment; patch identities cannot
approve PR creation. Production needs two humans including a release manager; security-critical
changes additionally need an independent security reviewer. A high-risk security exception must be
approved by a security reviewer who did not generate the patch. Deployment/rollback approver overlap
requires another authorized confirmation.

Expiry: plan 24 h, PR creation 4 h, production deploy 60 min, rollback 30 min, break glass 15 min.
MFA is required for PR/deploy/rollback/policy/security exceptions; production deploy/rollback
authentication is <=15 min old and policy-change authentication <=10 min.

Bind approval to organization, repository, run, action, base commit, patch/artifact digest, target
environment, policy version, expiry and approver. Any change invalidates it. Break glass is
severity-one only, requires two humans/fresh MFA/incident ID/justification/minimum scope, expires in
15 min, notifies security, never disables audit and requires review within two business days.

## Audit decision

Use append-only events with monotonic IDs, payload hashes, chained batches or Merkle roots, signed
checkpoints and trusted timestamps. Archive critical production approval/deploy/rollback/policy
events in S3 Object Lock compliance mode or equivalent WORM, replicate to DR and prevent application
identities from reducing retention/deleting locks. Provide offline verification. Auditors have
tenant-scoped read-only access; audit access is audited; exports include
hashes/signatures/schema/instructions; restricted evidence requires separate authorization. Search
supports organization, repository, run, actor, action, resource, digest, environment, IP address and
date range. General views redact source and secrets. Administrators cannot erase evidence.

## Binding quality and security gates

- Coverage: core 90% line/85% branch; authorization/approval/policy/redaction/state 95% branch;
  changed lines 90%; general services 80% line. Any reduction requires documented, scoped human
  approval with rationale, evidence, approver and expiry.
- Mutation: sensitive modules 85%, core 75%, overall 70%; no surviving critical
  authorization/approval mutant.
- Retrieval: Recall@20 90%, MRR@10 75%, symbol precision 95%, commit freshness 100%,
  cross-commit/tenant contamination 0%.
- Agents: requirement coverage 95%, hidden functional pass 85% before review, recovery 99%,
  duplicate effects/policy bypass/prompt-policy bypass 0%.
- Security recall: critical 100%, high 95%, overall 90%, secret recall 100%, critical sandbox escape
  blocking 100%.
- Critical, known-exploited, confirmed-secret, unsigned/unverifiable-image, missing-SBOM and
  missing-provenance conditions block. High blocks absent an unexpired exception; medium remediation
  <=30 days and low <=90 days.

## Consequences and verification

These are hard CI/release/deployment gates. Exceptions require scoped human approval, evidence,
compensating controls and expiry; they cannot waive approval, audit, tenant isolation, provenance or
fail-closed execution invariants.
