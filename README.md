# Autonomous Software Delivery Organization (ASDO)

> Production-oriented, provider-neutral platform for operating an autonomous multi-agent software
> engineering organization with deterministic policy gates, secure sandboxing, and immutable
> auditability.

---

## 1. What is ASDO?

The **Autonomous Software Delivery Organization (ASDO)** is an end-to-end, production-grade platform
that automates the entire software engineering lifecycle using specialized AI agents under strict
deterministic governance.

Unlike raw LLM wrappers or experimental coding bots, ASDO implements a **formal separation of
concerns**:

- **Generative AI models** _propose_ solutions, write code, formulate test cases, and analyze diffs.
- **Deterministic software invariants** (Open Policy Agent, PostgreSQL Row-Level Security, and
  cryptographic SHA-256 digest binding) _enforce_ authorization, tenant isolation, and approval
  policies.

### The Specialist Agent Team

ASDO coordinates six specialist agent roles orchestrated by a central **Coordinator Agent**:

- **Analyst Agent (`/requirements`):** Ingests raw requirements, clarifies ambiguities with
  interactive state machines, and generates verifiable Gherkin acceptance criteria.
- **Architect Agent (`/planning`):** Decomposes specifications into work packages, validates acyclic
  dependency graphs (DAGs), and enforces token/time budgets.
- **Coding Agent (`/patches`):** Writes code inside hardened, network-isolated sandboxes (Rootless /
  Firecracker) with path-traversal guards and generates cryptographically signed, content-addressed
  patches.
- **Testing Agent (`/security`):** Generates real test suites, computes mutation scores, detects
  test flakiness, and identifies test-weakening attempts.
- **Reviewer Agent (`/reviews`):** Performs read-only code review, threaded inline comment analysis,
  enforces strict separation of duties (authors cannot approve their own changes), and binds
  approvals to SHA-256 artifact digests.
- **Release Manager Agent (`/deployment`):** Executes Expand-Migrate-Contract schema migrations,
  canary traffic splitting with automated SLO health gates, purpose-separated deploy/rollback
  approvals, and automated post-rollback health checks.

---

## 2. Why Was It Built?

Traditional software engineering and generic AI assistants encounter four fundamental barriers:

1. **Unconstrained & Hallucinated Approvals:** LLMs cannot be trusted to self-authorize production
   changes. ASDO ensures that model outputs _never_ authorize actions; all access control and
   approval transitions are deterministic code.
2. **Security & Sandbox Escape Risks:** Running AI-generated code on host machines creates severe
   security vulnerabilities. ASDO executes code in rootless or Firecracker microVMs with drop-all
   network policies, read-only root filesystems, and secret canaries.
3. **Weakened Test Assertions:** AI assistants often delete or weaken assertions to make failing
   builds pass. ASDO pairs baseline/patched test attribution with mutation testing to detect and
   reject weakened tests.
4. **Operational Blind Spots:** ASDO provides WORM-compliant SHA-256 hash chains for audit logs,
   full OpenTelemetry distributed tracing, and automated rollback runbooks.

---

## 3. Where Can It Be Used?

ASDO is built with an **open-source-first, provider-neutral architecture**, enabling deployment
across any environment without vendor lock-in:

- **Local & On-Premise Workstations:** Docker Compose or local Kubernetes (`kind`/`k3s`) on Linux,
  macOS, or Windows WSL2.
- **Cloud Kubernetes Platforms:**
  - **AWS:** Amazon EKS, RDS (PostgreSQL with `pgvector`), S3, AWS Secrets Manager.
  - **Google Cloud:** GKE, Cloud SQL, Google Cloud Storage.
  - **Microsoft Azure:** AKS, Azure Database for PostgreSQL, Azure Blob Storage.
- **Air-Gapped & High-Compliance Environments:** Defense, banking, and healthcare organizations
  requiring self-hosted LLMs (via Ollama/vLLM/OpenAI-compatible gateways), private GitLab/GitHub
  Enterprise instances, and Keycloak-compatible OIDC.

---

## 4. Who Can Use This Project?

| Target Audience                    | Primary Use Case                                                                                                                                    |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Enterprise Engineering Teams**   | Automate backlog grooming, boilerplate generation, bug fixes, and continuous verification with human-in-the-loop approvals.                         |
| **Platform & DevOps Teams**        | Manage automated canary deployments, progressive rollouts, SLO gating, and disaster recovery drills.                                                |
| **Security & Compliance Officers** | Enforce zero-trust policy gates, strict separation of duties, cryptographically chained audit trails, and automatic secret/vulnerability scans.     |
| **Autonomous AI Research Labs**    | Benchmark multi-agent collaboration, evaluate coding model correctness against standardized evaluation datasets, and analyze token cost efficiency. |

---

## 5. Quick Start with Docker

### Full-Stack Platform in One Command

To launch all services (PostgreSQL with `pgvector`, Open Policy Agent, OpenTelemetry Collector,
FastAPI Backend, and Next.js Web Dashboard):

```bash
# 1. Build and export container requirements & images
pnpm build

# 2. Start all services in detached mode
docker compose -f compose.full.yaml up -d --wait

# 3. Check service health
docker compose -f compose.full.yaml ps
```

### Available Endpoints

- **Web UI & Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint:** [http://localhost:8000/health/live](http://localhost:8000/health/live)
- **Open Policy Agent (OPA):** [http://localhost:8181/v1/data](http://localhost:8181/v1/data)
- **PostgreSQL Database:** `127.0.0.1:55432`

See [`docs/docker-guide.md`](docs/docker-guide.md) for full container management commands, database
backup/restore procedures, and troubleshooting.

---

## 6. Local Development & Verification

### Prerequisites

- Node.js &gt;= 24.18.0 and Corepack (`pnpm` 11.22.0)
- Python 3.13.13 and `uv` &gt;= 0.11.7
- Docker Engine / Docker Desktop

### Setup & Verification Commands

```sh
# Enable corepack and install dependencies
corepack enable
pnpm bootstrap

# Start infrastructure dependencies (PostgreSQL, OPA, OTel Collector)
pnpm db:up

# Run database migrations
pnpm db:migrate

# Start local development servers (Next.js at :3000, FastAPI at :8000)
pnpm dev

# Execute the full verification suite (linting, typechecks, unit tests, security scans)
pnpm verify
```

---

## 7. Web Navigation Surface

| Route           | View Component         | Description                                                   |
| --------------- | ---------------------- | ------------------------------------------------------------- |
| `/`             | `FoundationStatusCard` | System health, OIDC status, and infrastructure metrics        |
| `/coordinator`  | `CoordinatorView`      | Multi-specialist agent orchestration pipeline                 |
| `/repositories` | `RepositoryBrowser`    | SCM repository explorer, AST symbols, and hybrid search       |
| `/requirements` | `RequirementsEditor`   | Requirements authoring, revisions, and clarification          |
| `/planning`     | `PlanViewer`           | Work package DAG visualization and budget tracking            |
| `/workflows`    | `WorkflowTimeline`     | Durable Temporal & LangGraph execution engine                 |
| `/patches`      | `DiffViewer`           | Sandboxed patch inspection and Monaco diff preview            |
| `/security`     | `SecurityDashboard`    | SARIF scanner, quality gates, and mutation scores             |
| `/reviews`      | `ReviewDashboard`      | Pull request reviews, threaded comments, and digest approvals |
| `/deployment`   | `DeploymentDashboard`  | Canary traffic rollout, SLO gates, and rollback controls      |
| `/evaluation`   | `EvaluationDashboard`  | 7-category readiness scorecards and token cost analytics      |

---

## 8. Documentation & Operational Runbooks

- [`docs/docker-guide.md`](docs/docker-guide.md): Comprehensive Docker operations and
  troubleshooting guide.
- [`docs/runbooks/rollback.md`](docs/runbooks/rollback.md): RB-001 Deployment Rollback & Reversal
  Procedure.
- [`docs/runbooks/disaster-recovery.md`](docs/runbooks/disaster-recovery.md): DR-001 Disaster
  Recovery & Backup Restoration (RPO &le; 15m, RTO &le; 60m).
- [`docs/runbooks/incident-response.md`](docs/runbooks/incident-response.md): IR-001 Incident
  Response & Break-Glass Protocol.
- [`docs/requirements-traceability.md`](docs/requirements-traceability.md): Requirements
  Traceability Matrix with passing executed evidence.
- [`docs/threat-model.md`](docs/threat-model.md): Comprehensive Threat Model and Security
  Countermeasures.
- [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md): Pinned Dependencies and Version
  Compatibility Matrix.
- [`docs/adr/`](docs/adr/): Architecture Decision Records (ADR-0001 through ADR-0005).

---

## License

Apache-2.0 License. See [`LICENSE`](LICENSE) for details.
