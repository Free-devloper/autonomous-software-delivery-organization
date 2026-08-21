import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RequirementsPage from "./page";

describe("RequirementsPage", () => {
  it("renders requirements page with header and editor", () => {
    render(<RequirementsPage />);

    expect(screen.getByRole("heading", { name: "Requirements Lifecycle" })).toBeVisible();
    expect(screen.getByText("Multi-Tenant OIDC & Worktree Security")).toBeVisible();
    expect(screen.getByTestId("version-badge")).toHaveTextContent("v1");
    expect(screen.getByTestId("status-badge")).toHaveTextContent("approved");
  });

  it("handles resolving clarification questions", () => {
    render(<RequirementsPage />);

    expect(screen.getByTestId("clarifications-banner")).toBeVisible();
    expect(
      screen.getByText("Which cryptographic signature algorithms are permitted for OIDC tokens?"),
    ).toBeVisible();

    // Resolve first clarification
    fireEvent.click(screen.getByText("RS256 only"));
    fireEvent.click(screen.getByTestId("clarification-submit-clar_auth_1"));

    expect(screen.getByText("Pending Clarification (1)")).toBeVisible();

    // Resolve second clarification
    fireEvent.click(screen.getByText("30 seconds"));
    fireEvent.click(screen.getByTestId("clarification-submit-clar_auth_2"));

    expect(screen.queryByTestId("clarifications-banner")).toBeNull();
  });

  it("creates a new requirement revision", () => {
    render(<RequirementsPage />);

    fireEvent.click(screen.getByTestId("new-revision-btn"));
    const titleInput = screen.getByTestId("revision-title-input");
    fireEvent.change(titleInput, { target: { value: "Multi-Tenant OIDC v2" } });
    fireEvent.click(screen.getByTestId("save-revision-btn"));

    expect(screen.getByText("Multi-Tenant OIDC v2")).toBeVisible();
    expect(screen.getByTestId("version-badge")).toHaveTextContent("v2");
    expect(screen.getByTestId("status-badge")).toHaveTextContent("draft");
  });
});
