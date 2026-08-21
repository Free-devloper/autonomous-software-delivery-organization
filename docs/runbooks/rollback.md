# Runbook: Deployment Rollback & Reversal Procedure

**Identifier:** RB-001  
**Category:** Delivery & Incident Mitigation  
**Governing Invariant:** All rollbacks require a distinct, purpose-bound rollback approval and
automated post-rollback verification.

---

## 1. Trigger Conditions

Rollback is initiated when:

1. **Canary SLO Breach:** Automated canary gates detect error rate > 0.1% or P99 latency > 200ms
   during canary validation window.
2. **Critical Defect / Data Corruption:** Critical runtime bug or data inconsistency identified
   post-promotion.
3. **Manual Operator Request:** Authorized Release Manager or On-Call Operator initiates rollback
   rehearsal or emergency mitigation.

---

## 2. Authorization & Separation of Duties Gate

- **Invariant:** A deploy approval cannot authorize a rollback.
- **Invariant:** The rollback requester cannot self-approve the rollback approval.
- **Required Roles:** `Role.RELEASE_MANAGER` or `Role.ORGANIZATION_ADMINISTRATOR`.

```bash
# 1. Request Rollback
POST /api/v1/deployment/plans/{plan_id}/rollback-request
{
  "target_digest": "<PREVIOUS_STABLE_SHA256_DIGEST>",
  "reason": "SLO latency threshold exceeded in staging/canary"
}

# 2. Submit Purpose-Bound Rollback Approval (Distinct Approver)
POST /api/v1/deployment/plans/{plan_id}/approvals
{
  "purpose": "rollback",
  "artifact_digest": "<PREVIOUS_STABLE_SHA256_DIGEST>",
  "notes": "Rollback authorized by secondary release manager"
}
```

---

## 3. Execution Procedure

1. **Traffic Draining:** Shift 100% of ingress traffic away from canary/failed pods back to the
   previous stable digest deployment.
2. **Container Image Rollback:** Argo CD / Helm updates container image digest back to the approved
   target digest.
3. **Database Schema Verification:**
   - Verify that expand-migrate-contract discipline was maintained.
   - If contract phase was not reached, schema remains backwards-compatible with previous code.
   - If rollback SQL exists, execute migration downgrade scripts.
4. **Trigger Rollback Execution:**

```bash
POST /api/v1/deployment/plans/{plan_id}/rollback-execute
```

---

## 4. Post-Rollback Automated Health Checks

The platform automatically executes and records 3 verification checks:

1. `schema_backward_compatibility`: Validates zero corrupted columns or constraint failures.
2. `worktree_state_consistency`: Validates code worktree state matches target Git commit.
3. `service_health_smoke`: Validates `/api/v1/health` live and ready endpoints return 200 OK.
