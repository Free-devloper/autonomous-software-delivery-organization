import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PlanningPage from "./page";

describe("PlanningPage", () => {
  it("renders planning page with header, budget cards, and work packages", () => {
    render(<PlanningPage />);

    expect(screen.getByRole("heading", { name: "Architecture & Work Packages" })).toBeVisible();
    expect(screen.getByText("Backend Token Verifier & Path Containment")).toBeVisible();
    expect(screen.getByText("Security & Penetration Test Suite")).toBeVisible();
    expect(screen.getByTestId("budget-tokens")).toHaveTextContent("50,000");
    expect(screen.getByTestId("plan-approval-badge")).toHaveTextContent("Pending Approval");
  });

  it("approves the architecture plan with rationale", () => {
    render(<PlanningPage />);

    const approveBtn = screen.getByTestId("approve-plan-btn");
    fireEvent.click(approveBtn);

    const input = screen.getByTestId("approval-rationale-input");
    fireEvent.change(input, { target: { value: "Decomposition verified against SRS §4" } });

    fireEvent.click(screen.getByTestId("confirm-approval-btn"));

    expect(screen.getByTestId("plan-approval-badge")).toHaveTextContent("Approved");
    expect(screen.getByTestId("approval-details")).toHaveTextContent(
      "Approved by usr_lead_architect: Decomposition verified against SRS §4",
    );
  });
});
