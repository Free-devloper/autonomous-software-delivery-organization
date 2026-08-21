# Runbook: Incident Response & Break-Glass Protocol

**Identifier:** IR-001  
**Category:** Security & Operations Governance  
**Governing Invariant:** All break-glass actions are recorded in immutable tamper-evident audit logs
with mandatory post-incident reviews.

---

## 1. Incident Severity Matrix

| Severity  | Definition                                                         | Target Response | Escalation Path                                    |
| --------- | ------------------------------------------------------------------ | --------------- | -------------------------------------------------- |
| **SEV-1** | Critical security compromise, data breach, or total outage         | &le; 15 minutes | Security Officer, Lead Architect, On-Call Engineer |
| **SEV-2** | Production degradation, canary SLO failure, non-critical data loss | &le; 30 minutes | Release Manager, Service Owner                     |
| **SEV-3** | Minor defect, flakiness, non-blocking bug                          | &le; 4 hours    | Owning Engineering Specialist                      |

---

## 2. Break-Glass Procedure (Emergency Access)

When normal multi-party approval or separation of duties cannot be completed due to critical
emergency outage:

1. **Activate Break-Glass Role:**
   - Account assumes temporary `Role.ORGANIZATION_ADMINISTRATOR` credentials with explicit audit
     reason annotation.
2. **Deterministic Audit Logging:**
   - Every break-glass action generates an immutable audit event with `action="auth.break_glass"`
     and SHA-256 state digest.
3. **Execution & Mitigation:**
   - Apply emergency hotfix or initiate rollback following `RB-001`.
4. **Automatic Expiry:**
   - Break-glass credentials expire automatically after 2 hours.

---

## 3. Post-Incident Review (PIR)

Within 48 hours of resolution:

- Export immutable audit trail from `/api/v1/audit/events`.
- Record Root Cause Analysis (RCA) and mitigation action items.
- Update threat model in `docs/threat-model.md` and risk register in `docs/risk-register.md`.
