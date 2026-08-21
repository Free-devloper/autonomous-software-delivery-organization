import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const ignoredDirectories = new Set([".git", ".next", ".tools", ".venv", "dist", "node_modules"]);
const forbiddenFiles = [/^\.env(?!\.example$)/u, /^(?:id_rsa|id_ed25519)$/u, /\.pem$/u, /\.p12$/u];
const secretPatterns = [
  { name: "private key", pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/u },
  { name: "GitHub token", pattern: /\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b/u },
  { name: "AWS access key", pattern: /\bAKIA[0-9A-Z]{16}\b/u },
];

const failures = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const fullPath = path.join(directory, entry.name);
    const relativePath = path.relative(process.cwd(), fullPath).replaceAll("\\", "/");
    if (entry.isDirectory()) {
      await walk(fullPath);
      continue;
    }
    if (!entry.isFile()) continue;
    if (forbiddenFiles.some((pattern) => pattern.test(entry.name))) {
      failures.push(`${relativePath}: forbidden secret-bearing filename`);
      continue;
    }
    const stat = await import("node:fs/promises").then(({ stat }) => stat(fullPath));
    if (stat.size > 2_000_000) continue;
    const contents = await readFile(fullPath, "utf8").catch(() => "");
    for (const { name, pattern } of secretPatterns) {
      if (pattern.test(contents)) failures.push(`${relativePath}: possible ${name}`);
    }
  }
}

await walk(process.cwd());
if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("No prohibited secret files or high-confidence secret patterns found.");
