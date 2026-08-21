import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DeploymentPage from "./page";

describe("DeploymentPage", () => {
  it("renders deployment dashboard with releases", () => {
    render(<DeploymentPage />);
    expect(screen.getByText("Progressive Delivery & Rollback")).toBeInTheDocument();
    expect(screen.getAllByText("v1.0.0 Production Release").length).toBeGreaterThanOrEqual(1);
  });

  it("handles canary promotion, deploy approvals and rollback rehearsals", () => {
    render(<DeploymentPage />);
    const promoteBtn = screen.getByTestId("promote-canary-btn");
    fireEvent.click(promoteBtn);

    const rollbackBtn = screen.getByTestId("request-rollback-btn");
    fireEvent.click(rollbackBtn);

    // Select pending plan rel-003 and approve deploy
    const plan3 = screen.getByTestId("plan-item-rel-003");
    fireEvent.click(plan3);

    const approveBtn = screen.getByTestId("approve-deploy-btn");
    fireEvent.click(approveBtn);
  });
});
