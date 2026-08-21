import { describe, expect, it } from "vitest";

import RootLayout, { metadata } from "./layout";

describe("RootLayout", () => {
  it("provides the document shell and stable metadata", () => {
    const layout = RootLayout({ children: <span>child content</span> });

    expect(layout.type).toBe("html");
    expect(layout.props).toMatchObject({ lang: "en" });
    expect(metadata.title).toBe("Autonomous Software Delivery Organization");
  });
});
