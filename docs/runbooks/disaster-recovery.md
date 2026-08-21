# Runbook: Disaster Recovery & Backup Restoration

**Identifier:** DR-001  
**Category:** Business Continuity & Resilience  
**SLO Targets:** Recovery Point Objective (RPO) &le; 15 minutes; Recovery Time Objective (RTO) &le;
60 minutes.

---

## 1. Backup Schedule & Architecture

1. **Relational Database (PostgreSQL):** Continuous WAL archiving to S3 with hourly snapshot
   manifests.
2. **Semantic Vector Index (pgvector):** Hourly index checkpointing.
3. **Audit Log Store:** Append-only, tamper-evident hash-chained audit snapshots.
4. **Digest Binding:** Every backup artifact is assigned a deterministic SHA-256 digest recorded in
   immutable metadata.

---

## 2. Trigger Conditions

- Primary database corruption or catastrophic infrastructure outage.
- Data center / cloud region loss.
- Periodic automated disaster recovery rehearsal drill (Phase 7 evaluation).

---

## 3. Step-by-Step Restoration Procedure

### Step 1: Select Target Backup Manifest

Query the evaluation service for the latest verified backup snapshot:

```bash
GET /api/v1/evaluation/backups
```

### Step 2: Provision Isolated Recovery Staging Environment

Deploy standard Helm baseline into the target standby namespace / cluster.

### Step 3: Execute Restore Drill

```bash
POST /api/v1/evaluation/restores
{
  "backup_id": "bkp-<ID>"
}
```

### Step 4: Verify Data Integrity & RTO Compliance

The recovery engine performs automated validation:

1. `observed_recovery_time_seconds` &le; 3600 (RTO requirement).
2. `data_integrity_verified` = true (row counts, checksums, and hash chain validation).
3. Schema sanity check against all active tenant partitions.

---

## 4. Post-Recovery Communication

- File disaster recovery completion report under `docs/dr-reports/`.
- Update `EvaluationReport` metrics for `recovery_readiness`.
