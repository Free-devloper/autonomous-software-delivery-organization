import { describe, expect, it } from "vitest";

import {
  fileContentResponseSchema,
  fileTreeResponseSchema,
  lexicalSearchResultSchema,
} from "../src/index";

describe("Repository contracts", () => {
  const sampleSha = "e4d909c290d0fb1ca068ffaddf22cbd0adddefec";

  it("validates a file tree response", () => {
    const validTree = {
      commit_sha: sampleSha,
      path: "src",
      entries: [
        { name: "main.ts", path: "src/main.ts", type: "file" as const, size_bytes: 1024 },
        { name: "utils", path: "src/utils", type: "directory" as const, size_bytes: 0 },
      ],
    };

    expect(fileTreeResponseSchema.parse(validTree)).toEqual(validTree);
  });

  it("validates a file content response", () => {
    const validContent = {
      commit_sha: sampleSha,
      path: "src/main.ts",
      content: "console.log('hello');",
      is_binary: false,
      size_bytes: 21,
      lines_count: 1,
    };

    expect(fileContentResponseSchema.parse(validContent)).toEqual(validContent);
  });

  it("validates a lexical search result", () => {
    const validSearch = {
      commit_sha: sampleSha,
      query: "hello",
      total_matches: 1,
      matches: [
        {
          path: "src/main.ts",
          line_number: 1,
          line_content: "console.log('hello');",
        },
      ],
    };

    expect(lexicalSearchResultSchema.parse(validSearch)).toEqual(validSearch);
  });
});
