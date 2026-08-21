import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath, URL } from "node:url";

const repositoryRoot = fileURLToPath(new URL("..", import.meta.url));

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
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

function assertContains(file, expected) {
  const text = readFileSync(join(repositoryRoot, file), "utf8");
  if (!text.includes(expected)) {
    throw new Error(`${file} is missing required text: ${expected}`);
  }
  return text;
}

function listFiles(directory) {
  const absolute = join(repositoryRoot, directory);
  const files = [];
  for (const entry of readdirSync(absolute, { withFileTypes: true })) {
    const path = join(absolute, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(relative(repositoryRoot, path)));
    } else if (entry.isFile()) {
      files.push(path);
    }
  }
  return files;
}

function validatePlatform() {
  const requiredFiles = [
    "apps/web/Dockerfile",
    "services/api/Dockerfile",
    "compose.yaml",
    "infra/otel/collector.yaml",
    "infra/opa/asdo.rego",
    "infra/helm/asdo/Chart.yaml",
    "infra/helm/asdo/values.yaml",
    "infra/argocd/asdo-local.yaml",
  ];
  for (const file of requiredFiles) {
    if (!existsSync(join(repositoryRoot, file))) {
      throw new Error(`${file} is required for Phase 0D`);
    }
  }

  assertContains("apps/web/Dockerfile", "@sha256:");
  assertContains("apps/web/Dockerfile", "USER 10001:10001");
  assertContains("apps/web/Dockerfile", "corepack pnpm install --frozen-lockfile");
  assertContains("apps/web/Dockerfile", "corepack pnpm --filter @asdo/web build");
  assertContains("services/api/Dockerfile", "@sha256:");
  assertContains("services/api/Dockerfile", "USER 10001:10001");
  assertContains("services/api/Dockerfile", "--require-hashes");
  assertContains("services/api/Dockerfile", "--no-deps");
  assertContains(".dockerignore", "!apps/web/.next/standalone/**/node_modules/**");
  assertContains("compose.yaml", "postgres:18.4@sha256:");
  assertContains("compose.yaml", "opentelemetry-collector-contrib:0.159.0@sha256:");
  assertContains("compose.yaml", "openpolicyagent/opa:1.19.1@sha256:");
  assertContains(
    "infra/helm/asdo/templates/_helpers.tpl",
    "production images require immutable digest",
  );
  assertContains("infra/helm/asdo/templates/networkpolicy.yaml", "kind: NetworkPolicy");
  assertContains(
    "infra/helm/asdo/templates/networkpolicy.yaml",
    "kubernetes.io/metadata.name: kube-system",
  );
  assertContains("infra/helm/asdo/templates/networkpolicy.yaml", 'component" "otel-collector');
  assertContains("infra/helm/asdo/templates/pdb.yaml", "kind: PodDisruptionBudget");
  assertContains("infra/helm/asdo/templates/hpa.yaml", "kind: HorizontalPodAutoscaler");
  assertContains("infra/helm/asdo/templates/_helpers.tpl", "app.kubernetes.io/instance:");
  assertContains("infra/helm/asdo/templates/api-configmap.yaml", 'include "asdo.fullname"');
  assertContains("infra/helm/asdo/templates/web-configmap.yaml", "NEXT_PUBLIC_ASDO_API_BASE_URL");
  assertContains("infra/helm/asdo/templates/api-deployment.yaml", "/api/v1/health/ready");
  assertContains(
    "infra/helm/asdo/templates/api-deployment.yaml",
    "api.existingSecretName is required",
  );
  assertContains(
    "infra/helm/asdo/templates/networkpolicy.yaml",
    "app.kubernetes.io/instance: {{ .Release.Name }}",
  );
  assertContains("infra/helm/asdo/templates/networkpolicy.yaml", "app.kubernetes.io/part-of: asdo");
  assertContains("infra/argocd/asdo-local.yaml", "automated: null");
  assertContains("package.json", "node scripts/container.mjs smoke");

  for (const file of listFiles("infra/helm/asdo/templates")) {
    const relative = file.replace(`${repositoryRoot}\\`, "").replaceAll("\\", "/");
    if (!relative.endsWith("deployment.yaml") && !relative.endsWith("otel-collector.yaml")) {
      continue;
    }
    const text = readFileSync(file, "utf8");
    for (const required of [
      "runAsNonRoot: true",
      "allowPrivilegeEscalation: false",
      "readOnlyRootFilesystem: true",
      "capabilities:",
      "- ALL",
      "resources:",
      "livenessProbe:",
      "readinessProbe:",
      "automountServiceAccountToken: false",
      "seccompProfile:",
    ]) {
      if (!text.includes(required)) {
        throw new Error(
          `${relative} is missing Kubernetes security/probe requirement: ${required}`,
        );
      }
    }
    if (!text.includes('include "asdo.componentLabels"')) {
      throw new Error(`${relative} is missing release-scoped instance labels/selectors`);
    }
  }
  console.log("Phase 0D platform artifacts passed static security validation.");
}

function devInfra() {
  run("docker", ["compose", "--file", "compose.yaml", "up", "--detach", "--wait"]);
}

const action = process.argv[2];

switch (action) {
  case "dev-infra":
    devInfra();
    break;
  case "deploy-local":
    validatePlatform();
    console.log("Local deployment validation completed without applying to a cluster.");
    break;
  case "smoke-test":
    run("uv", ["run", "python", "-m", "autonomous_sdo_api.smoke"]);
    break;
  case "test-platform":
    validatePlatform();
    break;
  default:
    console.error(
      "Usage: node scripts/platform.mjs <dev-infra|deploy-local|smoke-test|test-platform>",
    );
    process.exit(2);
}
