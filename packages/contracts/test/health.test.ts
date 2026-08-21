import { describe, expect, it } from "vitest";

import { healthLiveResponseSchema } from "../src/index";

describe("healthLiveResponseSchema", () => {
  it("accepts the stable version-one liveness contract", () => {
    expect(
      healthLiveResponseSchema.parse({ status: "ok", service: "api-test", api_version: "v1" }),
    ).toEqual({ status: "ok", service: "api-test", api_version: "v1" });
  });

  it("rejects unknown fields and invalid service identities", () => {
    expect(() =>
      healthLiveResponseSchema.parse({
        status: "ok",
        service: "API",
        api_version: "v1",
        tenant: "unexpected",
      }),
    ).toThrow();
  });
});
