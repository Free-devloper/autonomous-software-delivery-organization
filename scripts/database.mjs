import { spawnSync } from "node:child_process";
import { URL, fileURLToPath } from "node:url";

const repositoryRoot = fileURLToPath(new URL("..", import.meta.url));
const localDatabaseUrl = "postgresql+asyncpg://asdo_migrator:asdo-local-only@127.0.0.1:55432/asdo";
const localApplicationDatabaseUrl =
  "postgresql+asyncpg://asdo_app:asdo-app-local-only@127.0.0.1:55432/asdo";
const environment = {
  ...process.env,
  ASDO_API_DATABASE_URL: process.env.ASDO_API_DATABASE_URL ?? localDatabaseUrl,
  ASDO_TEST_DATABASE_URL: process.env.ASDO_TEST_DATABASE_URL ?? localApplicationDatabaseUrl,
};

function run(command, args, environmentOverrides = {}) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
    env: { ...environment, ...environmentOverrides },
    stdio: "inherit",
    shell: false,
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function capture(command, args, environmentOverrides = {}) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
    encoding: "utf8",
    env: { ...environment, ...environmentOverrides },
    shell: false,
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.stderr.write(result.stderr);
    process.exit(result.status ?? 1);
  }
  return result.stdout;
}

function compose(...args) {
  run("docker", ["compose", "--file", "compose.yaml", ...args]);
}

function composeCapture(...args) {
  return capture("docker", ["compose", "--file", "compose.yaml", ...args]);
}

function provisionLocalApplicationRole(databaseName) {
  const roleSql = `
DO $asdo$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'asdo_app') THEN
    CREATE ROLE asdo_app
      LOGIN PASSWORD 'asdo-app-local-only'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
  END IF;
END
$asdo$;
ALTER ROLE asdo_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT CONNECT ON DATABASE ${databaseName} TO asdo_app;
GRANT USAGE ON SCHEMA public TO asdo_app;
REVOKE ALL PRIVILEGES ON TABLE organizations FROM asdo_app;
GRANT SELECT, INSERT, UPDATE, DELETE
  ON TABLE organization_configurations
  TO asdo_app;
GRANT SELECT, INSERT
  ON TABLE audit_events
  TO asdo_app;
GRANT USAGE, SELECT
  ON SEQUENCE audit_events_sequence_id_seq
  TO asdo_app;
`;
  compose(
    "exec",
    "--no-TTY",
    "postgres",
    "psql",
    "--username",
    "asdo_migrator",
    "--dbname",
    databaseName,
    "--set",
    "ON_ERROR_STOP=1",
    "--command",
    roleSql,
  );
}

function alembic(databaseUrl, ...args) {
  run(
    "uv",
    ["run", "--package", "asdo-api", "alembic", "-c", "services/api/alembic.ini", ...args],
    {
      ASDO_API_DATABASE_URL: databaseUrl,
    },
  );
}

function migrate() {
  alembic(environment.ASDO_API_DATABASE_URL, "upgrade", "head");
  provisionLocalApplicationRole("asdo");
}

function ensureIntegrationDatabase() {
  const exists = composeCapture(
    "exec",
    "--no-TTY",
    "postgres",
    "psql",
    "--username",
    "asdo_migrator",
    "--dbname",
    "asdo",
    "--tuples-only",
    "--no-align",
    "--command",
    "SELECT 1 FROM pg_database WHERE datname = 'asdo_integration'",
  ).trim();
  if (exists !== "1") {
    compose(
      "exec",
      "--no-TTY",
      "postgres",
      "createdb",
      "--username",
      "asdo_migrator",
      "asdo_integration",
    );
  }
}

function testIntegration() {
  compose("up", "--detach", "--wait", "postgres");
  ensureIntegrationDatabase();

  const migrationUrl =
    "postgresql+asyncpg://asdo_migrator:asdo-local-only@127.0.0.1:55432/asdo_integration";
  const applicationUrl =
    "postgresql+asyncpg://asdo_app:asdo-app-local-only@127.0.0.1:55432/asdo_integration";
  const integrationEnvironment = {
    ASDO_API_DATABASE_URL: migrationUrl,
    ASDO_TEST_DATABASE_URL: applicationUrl,
  };

  alembic(migrationUrl, "upgrade", "head");
  const heads = capture(
    "uv",
    ["run", "--package", "asdo-api", "alembic", "-c", "services/api/alembic.ini", "heads"],
    integrationEnvironment,
  );
  process.stdout.write(heads);
  if (heads.split(/\r?\n/u).filter((line) => line.includes("(head)")).length !== 1) {
    console.error("Phase 0B requires exactly one Alembic head.");
    process.exit(1);
  }

  alembic(migrationUrl, "downgrade", "base");
  alembic(migrationUrl, "upgrade", "head");
  alembic(migrationUrl, "check");
  provisionLocalApplicationRole("asdo_integration");
  run("uv", ["run", "pytest", "services", "-m", "integration"], integrationEnvironment);
}

const action = process.argv[2];

switch (action) {
  case "up":
    compose("up", "--detach", "--wait", "postgres");
    break;
  case "down":
    compose("down", "--remove-orphans");
    break;
  case "migrate":
    migrate();
    break;
  case "test":
    testIntegration();
    break;
  default:
    console.error("Usage: node scripts/database.mjs <up|down|migrate|test>");
    process.exit(2);
}
