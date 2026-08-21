import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PatchesPage from "./page";

describe("PatchesPage", () => {
  it("renders page header, proposals sidebar, and default diff viewer", () => {
    render(<PatchesPage />);

    expect(screen.getByText("Content-Addressed Patches")).toBeInTheDocument();
    expect(screen.getByText("Phase 3C")).toBeInTheDocument();
    expect(
      screen.getAllByText("Add secure session token refreshing with exponential backoff").length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByTestId("proposal-card-patch-001")).toBeInTheDocument();
    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();
  });

  it("handles selecting another patch proposal", () => {
    render(<PatchesPage />);

    const secondCard = screen.getByTestId("proposal-card-patch-002");
    fireEvent.click(secondCard);

    expect(screen.getAllByText("pkg-rate-limits").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Add rate limiting headers to health API").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("handles applying a patch proposal", async () => {
    render(<PatchesPage />);

    const applyButton = screen.getByTestId("apply-patch-button");
    fireEvent.click(applyButton);

    expect(await screen.findByText("✓ Applied")).toBeInTheDocument();
  });
});
