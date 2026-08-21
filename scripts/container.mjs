/* global fetch, setTimeout */

import { spawnSync } from "node:child_process";
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

function capture(command, args) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
    encoding: "utf8",
    shell: false,
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(
      `${command} ${args.join(" ")} failed with exit ${result.status}:\n${result.stderr}`,
    );
  }
  return result.stdout.trim();
}

function buildImages() {
  run("uv", [
    "--quiet",
    "export",
    "--package",
    "asdo-api",
    "--frozen",
    "--no-dev",
    "--no-emit-project",
    "--format",
    "requirements.txt",
    "--output-file",
    "dist/asdo-api-requirements.txt",
  ]);
  run("docker", ["build", "--file", "services/api/Dockerfile", "--tag", "asdo-api:local", "."]);
  run("docker", ["build", "--file", "apps/web/Dockerfile", "--tag", "asdo-web:local", "."]);
}

function startContainer(image, port) {
  return capture("docker", [
    "run",
    "--detach",
    "--read-only",
    "--tmpfs",
    "/tmp",
    "--cap-drop",
    "ALL",
    "--security-opt",
    "no-new-privileges",
    "--user",
    "10001:10001",
    "--publish",
    `127.0.0.1::${port}`,
    image,
  ]);
}

function removeContainer(containerId) {
  spawnSync("docker", ["rm", "--force", containerId], {
    cwd: repositoryRoot,
    stdio: "ignore",
    shell: false,
  });
}

function containerHostPort(containerId, port) {
  const output = capture("docker", ["port", containerId, String(port)]);
  const match = output.match(/(?:127\.0\.0\.1|0\.0\.0\.0|\[::\]):(\d+)/u);
  if (!match) {
    throw new Error(`Could not resolve published port ${port} for ${containerId}: ${output}`);
  }
  return match[1];
}

function getContainerLogs(containerId) {
  const result = spawnSync("docker", ["logs", containerId], {
    cwd: repositoryRoot,
    encoding: "utf8",
    shell: false,
  });
  return `${result.stdout ?? ""}\n${result.stderr ?? ""}`.trim();
}

async function waitForHttp(url, containerId) {
  let lastError = "";
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  const logs = getContainerLogs(containerId);
  throw new Error(`Timed out waiting for ${url}: ${lastError}\nContainer logs:\n${logs}`);
}

async function smokeImage(image, port, path) {
  const containerId = startContainer(image, port);
  try {
    const hostPort = containerHostPort(containerId, port);
    await waitForHttp(`http://127.0.0.1:${hostPort}${path}`, containerId);
    const uid = capture("docker", ["exec", containerId, "sh", "-c", "id -u"]);
    if (uid !== "10001") {
      throw new Error(`${image} is running as uid ${uid}, expected 10001`);
    }
  } finally {
    removeContainer(containerId);
  }
}

async function smokeImages() {
  await smokeImage("asdo-api:local", 8000, "/api/v1/health/live");
  await smokeImage("asdo-web:local", 3000, "/");
  console.log("Container smoke checks passed for asdo-api:local and asdo-web:local.");
}

function isDockerAvailable() {
  const result = spawnSync("docker", ["info"], {
    cwd: repositoryRoot,
    stdio: "ignore",
    shell: false,
  });
  return result.status === 0;
}

if (!isDockerAvailable()) {
  console.log("Docker daemon is not available in this environment; skipping container step.");
  process.exit(0);
}

const action = process.argv[2];

switch (action) {
  case "build":
    buildImages();
    break;
  case "smoke":
    await smokeImages();
    break;
  default:
    console.error("Usage: node scripts/container.mjs <build|smoke>");
    process.exit(2);
}
