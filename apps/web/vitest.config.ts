import { defineConfig } from "vitest/config";

export default defineConfig({
  oxc: {
    jsx: {
      importSource: "react",
      runtime: "automatic",
    },
  },
  test: {
    coverage: {
      include: ["src/**/*.{ts,tsx}"],
      provider: "v8",
      reporter: ["text", "json-summary"],
      thresholds: { branches: 85, functions: 90, lines: 90, statements: 90 },
    },
    environment: "jsdom",
    globals: false,
    setupFiles: ["./test/setup.ts"],
  },
});
