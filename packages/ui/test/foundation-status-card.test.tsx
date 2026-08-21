import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FoundationStatusCard } from "../src/foundation-status-card";

describe("FoundationStatusCard", () => {
  it("exposes the foundation state as an accessible live status", () => {
    render(<FoundationStatusCard status="in-progress" updatedAt="2026-08-18T10:00:00Z" />);

    expect(screen.getByRole("heading", { name: "Engineering foundation" })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Engineering foundation in progress");
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });

  it("renders the supplied machine-readable update time", () => {
    render(<FoundationStatusCard status="ready" updatedAt="2026-08-18T12:00:00Z" />);

    expect(screen.getByRole("status")).toHaveTextContent("Engineering foundation ready");
    expect(screen.getByText("2026-08-18T12:00:00Z")).toHaveAttribute(
      "dateTime",
      "2026-08-18T12:00:00Z",
    );
  });
});
