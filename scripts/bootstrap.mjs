import { spawnSync } from "node:child_process";

const expected = {
  node: "v24.18.0",
  pnpm: "11.22.0",
  python: "3.13.13",
  uv: "0.11.7",
};

function capture(command, args) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    shell: process.platform === "win32",
  });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed: ${result.stderr.trim()}`);
  }
  return result.stdout.trim();
}

function run(command, args) {
  const result = spawnSync(command, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

const actual = {
  node: process.version,
  pnpm: capture("corepack", ["pnpm", "--version"]),
  uv: capture("uv", ["--version"]).split(/\s+/u)[1] ?? "",
};

for (const [tool, version] of Object.entries({
  node: expected.node,
  pnpm: expected.pnpm,
  uv: expected.uv,
})) {
  if (actual[tool] !== version) {
    throw new Error(`${tool} ${version} is required; found ${actual[tool] || "nothing"}`);
  }
}

run("corepack", ["pnpm", "install", "--frozen-lockfile"]);
run("uv", ["sync", "--frozen", "--all-groups", "--all-packages", "--all-extras"]);

const python = capture("uv", ["run", "--frozen", "python", "--version"]).replace(/^Python\s+/, "");
if (python !== expected.python) {
  throw new Error(`python ${expected.python} is required; found ${python || "nothing"}`);
}

console.log("Phase 0A dependencies match the committed lockfiles.");
