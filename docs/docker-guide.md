# Docker & Container Operations Guide

This guide provides end-to-end instructions for running, operating, and managing the **Autonomous
Software Delivery Organization (ASDO)** platform using Docker and Docker Compose.

---

## 1. Quick Start

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) &gt;= 24.0 (or Docker Desktop)
- [Docker Compose](https://docs.docker.com/compose/) v2 (e.g. `docker compose version`)
- Node.js &gt;= 24 and `pnpm` (if building images locally from source)
- Python 3.13 and `uv` (if exporting requirements locally)

### Build & Run the Entire Platform

To build all application containers and launch the full stack (PostgreSQL, OPA, OpenTelemetry
Collector, FastAPI API, and Next.js Web Portal):

```bash
# 1. Export dependencies and build local images
pnpm build:container

# 2. Start all services in the background
docker compose -f compose.full.yaml up -d --wait

# 3. Check service health
docker compose -f compose.full.yaml ps
```

Once running:

- **Web UI & Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **Open Policy Agent (OPA):** [http://localhost:8181/v1/data](http://localhost:8181/v1/data)
- **OTel Metrics & Tracing:** `localhost:4318` (HTTP) / `localhost:13133` (Health)
- **PostgreSQL Database:** `localhost:55432`

---

## 2. Infrastructure Services Only (Hybrid Local Development)

If you wish to run backend and frontend locally with hot reloading while hosting databases and
policy engines in Docker:

```bash
# Start infrastructure containers (PostgreSQL, OPA, OTel Collector)
pnpm infra:up

# Run database migrations
pnpm db:migrate

# Start local development servers
pnpm dev
```

To shut down infrastructure:

```bash
pnpm infra:down
```

---

## 3. Container Topology & Security Posture

| Container        | Image / Base                                         | Internal Port | Host Port   | Non-Root User | Read-Only Root FS | Security Controls                       |
| ---------------- | ---------------------------------------------------- | ------------- | ----------- | ------------- | ----------------- | --------------------------------------- |
| `postgres`       | `postgres:18.4@sha256:...`                           | 5432          | 55432       | 999:999       | No (Volume)       | Checksums enabled, memory tuned         |
| `opa`            | `openpolicyagent/opa:1.19.1@sha256:...`              | 8181          | 8181        | 65532:65532   | Yes               | `no-new-privileges`, read-only policies |
| `otel-collector` | `opentelemetry-collector-contrib:0.159.0@sha256:...` | 4318, 13133   | 4318, 13133 | 65532:65532   | Yes               | `no-new-privileges`, read-only config   |
| `api`            | `asdo-api:local` (Python 3.13 slim)                  | 8000          | 8000        | 10001:10001   | Yes               | `no-new-privileges`, unprivileged user  |
| `web`            | `asdo-web:local` (Node 24 slim)                      | 3000          | 3000        | 10001:10001   | Yes               | `no-new-privileges`, standalone build   |

All production images are digest-pinned (`@sha256:...`) and execute with dropped root capabilities.

---

## 4. Environment Variables Reference

Create a `.env` file or pass environment variables into the containers:

| Variable                           | Default Value                        | Description                                               |
| ---------------------------------- | ------------------------------------ | --------------------------------------------------------- |
| `ASDO_ENV`                         | `development`                        | Environment tier (`development`, `staging`, `production`) |
| `ASDO_DATABASE_URL`                | `postgresql+psycopg://...`           | PostgreSQL connection string with psycopg v3 driver       |
| `ASDO_OPA_URL`                     | `http://opa:8181/v1/data/asdo/authz` | Open Policy Agent evaluation endpoint                     |
| `ASDO_OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318`         | OpenTelemetry collector gRPC/HTTP endpoint                |
| `ASDO_ENABLE_TELEMETRY`            | `true`                               | Enable trace and metric reporting                         |
| `ASDO_LOG_LEVEL`                   | `INFO`                               | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)       |
| `NEXT_PUBLIC_API_URL`              | `http://127.0.0.1:8000`              | Backend API URL exposed to the frontend                   |

---

## 5. Daily Management Commands

### Viewing Logs

```bash
# Stream all logs
docker compose -f compose.full.yaml logs -f

# View backend API logs only
docker compose -f compose.full.yaml logs -f api

# View Next.js web logs only
docker compose -f compose.full.yaml logs -f web
```

### Checking Container Health

```bash
docker compose -f compose.full.yaml ps
```

### Executing Database Migrations

```bash
# Apply migrations inside the local environment
pnpm db:migrate

# Check migration status
pnpm db:status
```

### Taking a Database Backup

```bash
docker compose -f compose.full.yaml exec postgres pg_dump -U asdo_migrator -d asdo -F c -f /tmp/backup.dump
docker compose -f compose.full.yaml cp postgres:/tmp/backup.dump ./backup-$(date +%Y%m%d%H%M%S).dump
```

### Restoring from Database Backup

```bash
docker compose -f compose.full.yaml cp ./backup.dump postgres:/tmp/backup.dump
docker compose -f compose.full.yaml exec postgres pg_restore -U asdo_migrator -d asdo --clean /tmp/backup.dump
```

### Stopping and Cleaning Up

```bash
# Stop all services (retains volume data)
docker compose -f compose.full.yaml down

# Stop and wipe volume data (Fresh install)
docker compose -f compose.full.yaml down -v
```

---

## 6. Troubleshooting

- **PostgreSQL Connection Refused:** Verify that the `postgres` container is healthy
  (`docker compose -f compose.full.yaml ps postgres`) and that host port `55432` is not occupied by
  another instance.
- **OPA Policy Errors:** Verify the syntax of `.rego` files in [`infra/opa/`](../infra/opa/) and
  check `docker compose -f compose.full.yaml logs opa`.
- **API Health Check Failure:** Inspect `docker compose -f compose.full.yaml logs api` to confirm
  database connectivity and environment variables.
