import { describe, expect, it } from "vitest";

import {
  codeSymbolSchema,
  fileSymbolsResponseSchema,
  symbolKindSchema,
  symbolLocationSchema,
} from "../src/index";

describe("Symbols contracts", () => {
  const sampleSha = "e4d909c290d0fb1ca068ffaddf22cbd0adddefec";

  it("validates symbol location schema", () => {
    const loc = {
      start_line: 10,
      start_column: 0,
      end_line: 25,
      end_column: 1,
    };
    expect(symbolLocationSchema.parse(loc)).toEqual(loc);
  });

  it("validates code symbol schema", () => {
    const symbol = {
      id: "sym_123",
      name: "calculateTotal",
      qualified_name: "billing.calculateTotal",
      kind: "function" as const,
      location: {
        start_line: 1,
        start_column: 0,
        end_line: 5,
        end_column: 1,
      },
      docstring: "Calculate the total invoice amount.",
      is_exported: true,
    };
    expect(codeSymbolSchema.parse(symbol)).toEqual(symbol);
  });

  it("validates file symbols response schema", () => {
    const response = {
      commit_sha: sampleSha,
      file_path: "src/billing.ts",
      language: "typescript",
      symbols: [
        {
          id: "sym_1",
          name: "Invoice",
          qualified_name: "Invoice",
          kind: "class" as const,
          location: { start_line: 1, start_column: 0, end_line: 20, end_column: 1 },
          is_exported: true,
        },
        {
          id: "sym_2",
          name: "getBalance",
          qualified_name: "Invoice.getBalance",
          kind: "method" as const,
          location: { start_line: 5, start_column: 2, end_line: 8, end_column: 3 },
          parent_id: "sym_1",
          is_exported: false,
        },
      ],
    };
    expect(fileSymbolsResponseSchema.parse(response)).toEqual(response);
  });

  it("rejects invalid symbol kinds", () => {
    expect(() => symbolKindSchema.parse("invalid_kind")).toThrow();
  });
});
