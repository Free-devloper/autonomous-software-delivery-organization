import { describe, expect, it } from "vitest";

import { parsePublicWebConfig } from "../src/index";

describe("parsePublicWebConfig", () => {
  it("normalizes a valid public API base URL", () => {
    expect(
      parsePublicWebConfig({
        NEXT_PUBLIC_ASDO_API_BASE_URL: "https://api.example.test/api/v1/",
        NEXT_PUBLIC_ASDO_ENVIRONMENT: "staging",
      }),
    ).toEqual({ apiBaseUrl: "https://api.example.test/api/v1", environment: "staging" });
  });

  it("rejects an unapproved environment", () => {
    expect(() =>
      parsePublicWebConfig({
        NEXT_PUBLIC_ASDO_API_BASE_URL: "https://api.example.test/api/v1",
        NEXT_PUBLIC_ASDO_ENVIRONMENT: "preview",
      }),
    ).toThrow();
  });

  it("rejects credentials embedded in an HTTP URL", () => {
    expect(() =>
      parsePublicWebConfig({
        NEXT_PUBLIC_ASDO_API_BASE_URL: "https://user:password@api.example.test",
        NEXT_PUBLIC_ASDO_ENVIRONMENT: "local",
      }),
    ).toThrow();
  });
});
