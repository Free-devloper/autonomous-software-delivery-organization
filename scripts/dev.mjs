import { spawn } from "node:child_process";

const shell = process.platform === "win32";
const children = [
  spawn("corepack", ["pnpm", "--filter", "@asdo/web", "dev"], {
    stdio: "inherit",
    shell,
  }),
  spawn(
    "uv",
    ["run", "uvicorn", "autonomous_sdo_api.app:app", "--app-dir", "services/api/src", "--reload"],
    { stdio: "inherit", shell },
  ),
];

let stopping = false;
function stop(signal) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill(signal);
}

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));

for (const child of children) {
  child.on("exit", (code) => {
    stop("SIGTERM");
    process.exitCode = code ?? 1;
  });
}
