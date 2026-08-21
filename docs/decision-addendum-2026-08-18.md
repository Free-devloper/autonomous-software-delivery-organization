# Product Owner Decision Addendum

- **Version:** 1.0
- **Approved:** 2026-08-18
- **Status:** Binding supplement to the authoritative `project_doc.txt` requirements baseline
- **Evidence state:** Decisions approved; Phase 0A and initial Phase 0B evidence is tracked in
  `docs/requirements-traceability.md`; later milestones remain unverified

Each `DEC-*` row is an independently traceable requirement derived from the product owner's approved
sections 2-13. Planned paths are forecasts. Evidence remains `Planned` until the stated tests are
executed successfully.

## Repository and governance

| ID           | Requirement                                                                                                                                                                   | Milestone / planned paths | Planned verification                                       |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------- |
| DEC-REPO-001 | Create private GitHub repository `autonomous-software-delivery-organization` in the supplied organization; use a monorepo and Apache-2.0 unless changed before public release | 0A / root, `LICENSE`      | Repository/API inspection; license check                   |
| DEC-REPO-002 | Protected default `main`; short-lived feature branches; PR-only changes; no direct commits or force pushes                                                                    | 0A / GitHub rules, docs   | GitHub ruleset contract/live tests and rejected push tests |
| DEC-REPO-003 | Merge requires passing CI/security scanning and at least two human approvals                                                                                                  | 0A, 5B / CI, policy       | Ruleset inspection and merge-gate negative tests           |
| DEC-REPO-004 | Release commits are signed and production artifacts retain provenance                                                                                                         | 0A, 6B / CI/release       | Unsigned release rejection and signature verification      |
| DEC-REPO-005 | Enable Dependabot or Renovate with reviewed automated updates                                                                                                                 | 0A / provider config      | Configuration validation and update PR contract test       |

## Deployment, environments, reliability and cost

| ID            | Requirement                                                                                                                                                                       | Milestone / planned paths    | Planned verification                                            |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------- |
| DEC-PLAT-001  | Cloud-neutral Kubernetes architecture with AWS reference: EKS `eu-central-1`, DR `eu-west-1`, ECR, S3, Route 53, CloudFront/WAF, KMS and provider-neutral OpenBao/Secrets Manager | 0D, 6B / `infra/`, adapters  | Module/contract tests and staging AWS conformance               |
| DEC-PLAT-002  | Environments: local Compose+kind, ephemeral PR CI namespace, shared development, production-equivalent staging, isolated production and warm DR                                   | 0D, 6B / config, Helm/Argo   | Environment schema, namespace/account isolation and smoke tests |
| DEC-PLAT-003  | Separate accounts where practical; production separate cluster/database; no shared production/non-production credentials                                                          | 0D / infra/policy            | Credential-boundary, topology and policy tests                  |
| DEC-PLAT-004  | Argo CD GitOps, immutable production image digests and OpenTofu/Terraform-compatible infrastructure                                                                               | 0D, 6B / `infra/`            | Render/plan/sync, mutable-tag rejection and drift tests         |
| DEC-SCALE-001 | Certify 1,000 organizations, 10,000 repositories, 500 concurrent runs, 2,000 sandboxes, 10,000 sessions, 50,000 events/s, 100M chunks and repos up to 20 GB/5M lines              | 7B / performance/evaluation  | Versioned target-load report for every limit                    |
| DEC-SLO-001   | Availability: control plane 99.9% monthly; approval/audit reads 99.95%; privileged audit capture 100%                                                                             | 0D, 7B / SLO/telemetry       | SLI calculation, alert and fault-injection evidence             |
| DEC-SLO-002   | p95: read API <400 ms; write API <800 ms excluding external work; events <2 s; certified search <1.5 s                                                                            | 7B / performance tests       | Target-load latency histograms and regression gates             |
| DEC-SLO-003   | Interrupted recovery >=99% and privileged trace completeness >=95%                                                                                                                | 2C, 7A / workflow/evaluation | Recovery trials and trace completeness audit                    |
| DEC-COST-001  | Per-organization monthly and per-run budgets; estimate before run; warn 75%, hard stop 100%, unaccounted spend <5%                                                                | 2B, 7B / budget/policy/UI    | Boundary/property, UI and accounting reconciliation tests       |
| DEC-COST-002  | Cache reuse only when tenant, authorization, model version and content digest match                                                                                               | 2B / gateway/cache           | Cross-context cache-poisoning and authorization tests           |
| DEC-DR-001    | RPO/RTO: DB 5 min/60 min; acknowledged audit/approvals target zero RPO; artifacts 15 min RPO; regional RTO 4 h; Git config zero RPO                                               | 7C / backup/DR               | Measured restore/failover evidence per objective                |
| DEC-DR-002    | Warm standby, encrypted artifact replication, PITR, versioned GitOps; quarterly restore, semiannual regional failover, annual full DR exercise                                    | 6B, 7C / infra/runbooks      | Scheduled exercise reports and remediation tracking             |

## Source control, models and embeddings

| ID            | Requirement                                                                                                                        | Milestone / planned paths    | Planned verification                                               |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------ |
| DEC-SCM-001   | Support GitHub first and GitLab before final production release through one provider-neutral interface                             | 1A, 5C / repository adapters | Shared contract suite plus live-provider evidence                  |
| DEC-SCM-002   | Dedicated GitHub test org and GitLab group/instance with synthetic public/private repos; never destructively test production repos | 1A, 5C / fixtures/config     | Target allowlist and destructive-operation rejection tests         |
| DEC-SCM-003   | Contract servers may replace unavailable credentials during development, but live verification remains mandatory                   | 1A, 5C / contract tests      | Evidence gate rejects provider-complete status without live result |
| DEC-MODEL-001 | Gateway supports OpenAI-, Anthropic- and Gemini-compatible APIs, local vLLM and development-only Ollama                            | 2B / model gateway           | Provider contracts, capability matrix and environment-policy tests |
| DEC-MODEL-002 | Provider/model selection is configurable per organization/repository; private deployments support offline/local processing         | 2B / policy/config           | Tenant configuration, egress-denial and offline E2E tests          |
| DEC-MODEL-003 | Restricted content never reaches external models; prompt/source/output retention and redaction are configurable                    | 2B, 4D / policy/redaction    | Classification egress and redaction/retention tests                |
| DEC-EMB-001   | Embeddings support commercial APIs, preferred BGE-M3, maintained E5 alternative and local vLLM/TEI-compatible serving              | 1D / embedding adapters      | Adapter/capability and local-offline contract tests                |
| DEC-EMB-002   | Store embedding model ID/revision/dimensions/content hash/source commit; model changes trigger controlled re-indexing              | 1D / index metadata/workflow | Schema, cross-commit and re-index state-machine tests              |

## Tenancy

| ID          | Requirement                                                                                                               | Milestone / planned paths  | Planned verification                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------ |
| DEC-TEN-001 | Support shared-control-plane multi-tenant SaaS first and dedicated single-tenant installs from identical code/Helm charts | 0B, 0D / services, Helm    | Deployment/profile and configuration equivalence tests |
| DEC-TEN-002 | Every tenant record has organization identity and PostgreSQL RLS enforces isolation                                       | 0B / schema/migrations     | Cross-tenant SQL and pooled-context tests              |
| DEC-TEN-003 | Tenant-scope object paths/encryption contexts, cache keys, streams, vectors, logs and metrics                             | 0B-0D / adapters/telemetry | Cross-tenant matrix for every store/signal             |
| DEC-TEN-004 | High-security customers can use isolated cluster/database/account                                                         | 0D, 6B / infra profiles    | Dedicated-profile render/deploy/isolation tests        |

## Compliance, residency, classification, retention and encryption

| ID            | Requirement                                                                                                                                                                | Milestone / planned paths      | Planned verification                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------ |
| DEC-COMP-001  | Design evidence for SOC 2 Type II, ISO 27001, GDPR, CCPA/CPRA, OWASP ASVS L2, NIST SSDF and SLSA-compatible provenance; never claim certification without authorized audit | 0D-7D / controls/docs/evidence | Control-to-evidence audit and certification-claim review                       |
| DEC-DATA-001  | Organization selects approved data region; source, embeddings, artifacts, DB and backups remain there absent explicit authorization                                        | 0B-0D / policy/storage/infra   | Region-policy, replication and egress tests                                    |
| DEC-DATA-002  | Cross-region telemetry is aggregated and stripped of source, prompts, secrets and personal data; dedicated installs support customer residency                             | 0D / telemetry/export          | Canary/redaction/region-route tests                                            |
| DEC-CLASS-001 | Enforce Public, Internal, Confidential and Restricted classifications across storage, retrieval, models and UI                                                             | 0B-4D / contracts/policy       | Classification transition and enforcement matrix                               |
| DEC-CLASS-002 | Restricted data never reaches external models, never includes secrets/private keys in prompts, uses approved encrypted stores, fresh authorized roles and audited access   | 0C-4D / policy/gateway/audit   | Restricted-data egress, secret-canary, fresh-auth and audit-completeness tests |
| DEC-RET-001   | Requirements/plans/traceability retain 3 years; runs 1 year; sandbox logs 90 days; prompts/responses 30 days default                                                       | 0B, 2C, 3B / lifecycle policy  | Clock/lifecycle/deletion/legal-hold tests                                      |
| DEC-RET-002   | Findings retain 3 years after closure; approvals/deployments/audit 7 years                                                                                                 | 0B, 4C-6C / lifecycle/WORM     | Closure/retention and locked-record tests                                      |
| DEC-RET-003   | Delete temporary worktrees/sandboxes within 24 h and unreferenced intermediates within 30 days                                                                             | 3A-3C / cleanup workflows      | Time-advance, retry and orphan cleanup tests                                   |
| DEC-RET-004   | Backups retain 35 daily, 12 monthly and 7 annual points; legal holds override expiry                                                                                       | 7C / backup policy             | Retention schedule, locked hold and attempted deletion tests                   |
| DEC-ENC-001   | TLS 1.3 where supported, TLS 1.2 minimum; AES-256-equivalent at rest; KMS/OpenBao envelope encryption                                                                      | 0D / ingress/storage/secrets   | Protocol/cipher/config and encrypted-object tests                              |
| DEC-ENC-002   | Separate production/non-production keys, optional tenant enterprise keys, automated credential rotation and policy-driven key rotation without contract rewrites           | 0D / key/secrets adapters      | Cross-environment key rejection, lease/rotation and compatibility tests        |

## Sandbox isolation

| ID          | Requirement                                                                                                                              | Milestone / planned paths | Planned verification                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------- |
| DEC-SBX-001 | Firecracker-capable KVM Linux exists in staging/production on dedicated tainted sandbox node pools; control-plane workloads are excluded | 3A / sandbox infra        | Node scheduling/admission and actual KVM profile tests              |
| DEC-SBX-002 | Restrictive security groups/network policy, ephemeral disks, post-task microVM/worktree destruction                                      | 3A-3B / sandbox/policy    | Network escape, persistence and cleanup failure tests               |
| DEC-SBX-003 | Attest Firecracker version, kernel, rootfs digest and sandbox policy for every execution                                                 | 3A / attestations         | Schema, digest substitution and missing-attestation rejection tests |
| DEC-SBX-004 | Rootless fallback only local/CI/approved trusted repos; never untrusted public production; missing KVM fails closed                      | 3A-3B / runtime policy    | Classification matrix and silent-downgrade rejection tests          |

## Roles, authentication, approvals and break glass

| ID           | Requirement                                                                                                                                                                                               | Milestone / planned paths           | Planned verification                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| DEC-IAM-001  | Implement organization owner/admin, repository admin, requester, maintainer, security reviewer, release manager, run operator, auditor, billing admin, read-only viewer and service account roles         | 0C / identity/policy                | Full role-action-resource-tenant matrix                                   |
| DEC-APR-001  | Agents never approve; patch identity cannot approve PR creation; requester cannot approve own production deployment                                                                                       | 0C, 5B / approval policy            | Self/model/patch-author approval-confusion tests                          |
| DEC-APR-002  | Production requires two humans including a release manager; security-critical changes also require security reviewer approval                                                                             | 5B, 6B / policy/workflow            | Role-combination and missing-approval negative tests                      |
| DEC-APR-003  | High-risk security exception requires a security reviewer who did not generate the patch                                                                                                                  | 4C, 5B / exception/approval policy  | Patch-author exception rejection and identity provenance tests            |
| DEC-APR-004  | Same release manager may approve deploy/rollback only with confirmation from another authorized reviewer                                                                                                  | 6B-6C / release policy              | Same-actor, missing-confirmation and replay tests                         |
| DEC-APR-005  | Expiry: plan 24 h; PR creation 4 h; production deploy 60 min; rollback 30 min; break glass 15 min                                                                                                         | 2C, 5B, 6C / approval schema        | Boundary/time-skew/expiry property tests                                  |
| DEC-AUTH-001 | MFA session required for PR/deploy/rollback/policy/security exception; production deploy/rollback auth <=15 min and policy-change auth <=10 min                                                           | 0C, 5B-6C / auth policy             | MFA/age/revocation/stale-session tests                                    |
| DEC-APR-006  | Bind approval to org, repo, run, action, base commit, patch/artifact digest, target environment, policy version, expiry and approver; any change invalidates                                              | 5B-6C / approval schema/state       | One-field-at-a-time substitution/replay property suite                    |
| DEC-BG-001   | Break glass only severity-one; two humans, fresh MFA, incident ID/justification/minimum scope; auto-expire 15 min; immediate security notification; audit never disabled; review within two business days | 0C, 6C / policy/audit/notifications | Precondition, expiry, notification, audit-continuity and review-SLA tests |

## Immutable audit

| ID          | Requirement                                                                                                                                                                  | Milestone / planned paths | Planned verification                                              |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------- |
| DEC-AUD-001 | Retain approval/deploy/rollback/policy/privileged/security-exception audit 7 years; ordinary operational audit >=3 years; legal hold overrides expiry                        | 0C / audit lifecycle      | Retention/hold/deletion tests                                     |
| DEC-AUD-002 | Append-only events with monotonic IDs, payload hash, chained batches/Merkle roots, signed periodic checkpoints and trusted timestamps                                        | 0C / audit service        | Update/delete/backdate/gap/hash-chain/signature tests             |
| DEC-AUD-003 | Store verification metadata separately and provide offline audit verification command                                                                                        | 0C / audit verifier       | Independent fixture verification and tamper rejection             |
| DEC-AUD-004 | Critical production approval/deploy/rollback/policy records use S3 Object Lock-equivalent compliance WORM, replicate to DR and cannot be shortened/deleted by app identities | 0D, 6B / archive/infra    | Retention-reduction, delete-denial, replication and restore tests |
| DEC-AUD-005 | Auditor access is read-only and organization scoped; audit access is audited; general views redact source/secrets; restricted evidence needs separate authorization          | 0C / API/policy/UI        | Cross-tenant/access-recursion/redaction/fresh-authorization tests |
| DEC-AUD-006 | Exports contain hashes/signatures/schema/instructions and search supports org, repo, run, actor, action, resource, digest, environment, IP and date range                    | 0C / audit API/export     | Query contract, export schema and offline verification tests      |
| DEC-AUD-007 | Production administrators cannot modify or erase audit evidence                                                                                                              | 0C / policy/storage       | Privileged-admin negative/tamper tests                            |

## Quality and security thresholds

| ID                | Requirement                                                                                                                                                        | Milestone / planned paths          | Planned verification                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- | --------------------------------------------------------- |
| DEC-COV-001       | Core >=90% line/85% branch; sensitive auth/approval/policy/redaction/state >=95% branch; changed lines >=90%; general services >=80% line                          | 0A, 4B / CI/evaluation             | Coverage fixtures and threshold boundary tests            |
| DEC-COV-002       | Any coverage reduction requires documented scoped approval with rationale, evidence, approver and expiry                                                           | 4B / CI/approval evidence          | Unauthorized/expired/incomplete reduction rejection tests |
| DEC-MUT-001       | Mutation: sensitive >=85%, core >=75%, overall >=70%; no surviving critical auth/approval mutant                                                                   | 4B / mutation policy               | Seeded mutants and threshold/critical-survivor gates      |
| DEC-RETVAL-001    | Retrieval Recall@20 >=90%, MRR@10 >=75%, symbol precision >=95%, commit freshness 100%, cross-commit and cross-tenant contamination 0%                             | 1D, 7A / retrieval evaluation      | Versioned golden datasets and contamination suites        |
| DEC-AGENT-001     | Requirement coverage >=95%, hidden functional pass >=85% before review, interrupted recovery >=99%, duplicate side effects/approval bypass/prompt-policy bypass 0% | 2B-7A / agent evaluation           | Versioned hidden/adversarial/replay datasets              |
| DEC-SECRECALL-001 | Seeded vulnerability recall: critical 100%, high >=95%, overall >=90%; secrets 100%; critical sandbox escape block 100%                                            | 4C-7A / security evaluation        | Seeded corpus and actual sandbox profiles                 |
| DEC-VULN-001      | Critical, known-exploited, confirmed-secret, unsigned/unverifiable image, missing SBOM or missing provenance blocks                                                | 4C, 6B / policy/CI/admission       | Known-bad fixtures and admission negative tests           |
| DEC-VULN-002      | High blocks without unexpired exception; medium plan <=30 days; low plan <=90 days; confirmed secrets trigger immediate revocation                                 | 4C / findings/exception/revocation | Severity/SLA/expiry/revocation workflow tests             |

## Compatibility

| ID              | Requirement                                                                                                                 | Milestone / planned paths  | Planned verification                                   |
| --------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------ |
| DEC-COMPAT-001  | Support current and previous major API; additive changes within major; breaking removal notice >=180 days                   | 0A, 6A / contracts/release | API diff, old-client and deprecation-policy tests      |
| DEC-COMPAT-002  | Database supports at least one rolling-deployment version boundary                                                          | 0B, 6A / migrations        | Old/new mixed-version and expand-contract tests        |
| DEC-COMPAT-003  | Temporal changes replay deterministically against retained histories                                                        | 2C / workflow fixtures     | Replay suite across every workflow change              |
| DEC-LANG-001    | Tier one TS/JS, Python, Go, Java/Kotlin receives full parsing, symbols, tests and security analysis                         | 1C-4C / indexer/tooling    | Language corpus and capability conformance tests       |
| DEC-LANG-002    | Also support Rust, C#, C/C++, Ruby, PHP, SQL, Bash, YAML, JSON, HCL and Dockerfile; partial/lexical limitations are visible | 1B-4C / adapters/UI/docs   | Per-language capability matrix and UI limitation tests |
| DEC-BROWSER-001 | Support latest two stable Chrome, Firefox, Edge and Safari                                                                  | 0A onward / Playwright/UI  | Browser matrix E2E/accessibility suite                 |
| DEC-ARCH-001    | Support Linux `amd64` and `arm64`; Firecracker may start `amd64` but `arm64` remains architectural/roadmap requirement      | 0D, 3A / images/sandbox    | Multi-arch image and supported-profile tests           |
| DEC-DEV-001     | Developer workstations: Linux, macOS and Windows via WSL2                                                                   | 0A / bootstrap/docs        | Clean-machine bootstrap and command verification       |

## Approval status

Phase 0 local implementation approval was received after this addendum was created. The GitHub
organization is `roytechworkforce`, and `project_doc.txt` is confirmed as the only complete
authoritative project document. This addendum does not authorize production deployment, destructive
operations or external writes beyond milestone-specific approval.
