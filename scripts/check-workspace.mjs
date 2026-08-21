import { access, readFile } from "node:fs/promises";

const requiredFiles = [
  "apps/web/package.json",
  "packages/config/package.json",
  "packages/contracts/package.json",
  "packages/ui/package.json",
  "services/api/pyproject.toml",
];

const packageNames = new Set();
for (const file of requiredFiles) {
  await access(file);
  if (!file.endsWith("package.json")) continue;
  const manifest = JSON.parse(await readFile(file, "utf8"));
  if (typeof manifest.name !== "string" || manifest.name.length === 0) {
    throw new Error(`${file} must declare a package name`);
  }
  if (packageNames.has(manifest.name)) throw new Error(`duplicate package name: ${manifest.name}`);
  packageNames.add(manifest.name);
}

const root = JSON.parse(await readFile("package.json", "utf8"));
if (root.private !== true) throw new Error("the monorepo root must remain private");
if (root.packageManager !== "pnpm@11.22.0") {
  throw new Error("packageManager must pin pnpm@11.22.0");
}

console.log(
  `Workspace structure is valid (${packageNames.size} JavaScript packages, 1 Python service).`,
);
