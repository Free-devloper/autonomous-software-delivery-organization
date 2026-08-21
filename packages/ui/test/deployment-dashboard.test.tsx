import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DeploymentDashboard, type ReleasePlanDisplay } from "../src/deployment-dashboard";

describe("DeploymentDashboard", () => {
  const mockPlans: ReleasePlanDisplay[] = [
    {
      id: "rel-001",
      title: "v1.0.0 Production Release",
      version: "1.0.0",
      artifact_digest: "a".repeat(64),
      artifact_image: "ghcr.io/org/asdo:1.0.0",
      strategy: "canary",
      target_environment: "production",
      status: "canary_validating",
      canary_weight_percentage: 25,
      slo_passed_count: 2,
      slo_total_count: 2,
    },
    {
      id: "rel-002",
      title: "v0.9.0 Staging Release",
      version: "0.9.0",
      artifact_digest: "b".repeat(64),
      artifact_image: "ghcr.io/org/asdo:0.9.0",
      strategy: "rolling",
      target_environment: "staging",
      status: "completed",
    },
    {
      id: "rel-003",
      title: "v0.8.0 Rolled Back Release",
      version: "0.8.0",
      artifact_digest: "c".repeat(64),
      artifact_image: "ghcr.io/org/asdo:0.8.0",
      strategy: "blue_green",
      target_environment: "development",
      status: "rolled_back",
    },
  ];

  it("renders stat cards and release plan list", () => {
    render(<DeploymentDashboard plans={mockPlans} />);
    expect(screen.getByTestId("deployment-dashboard")).toBeInTheDocument();
    expect(screen.getAllByText("v1.0.0 Production Release").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("v0.9.0 Staging Release").length).toBeGreaterThanOrEqual(1);
  });

  it("handles plan selection and action buttons", () => {
    const onSelectPlan = vi.fn();
    const onPromoteCanary = vi.fn();
    const onRequestRollback = vi.fn();

    render(
      <DeploymentDashboard
        plans={mockPlans}
        selectedPlanId="rel-001"
        onSelectPlan={onSelectPlan}
        onPromoteCanary={onPromoteCanary}
        onRequestRollback={onRequestRollback}
      />,
    );

    const promoteBtn = screen.getByTestId("promote-canary-btn");
    fireEvent.click(promoteBtn);
    expect(onPromoteCanary).toHaveBeenCalledWith("rel-001");

    const rollbackBtn = screen.getByTestId("request-rollback-btn");
    fireEvent.click(rollbackBtn);
    expect(onRequestRollback).toHaveBeenCalledWith("rel-001");

    const planItem = screen.getByTestId("plan-item-rel-002");
    fireEvent.click(planItem);
    expect(onSelectPlan).toHaveBeenCalledWith("rel-002");
  });

  it("renders approve deploy button for pending plans", () => {
    const onApproveDeploy = vi.fn();
    const pendingPlan: ReleasePlanDisplay = {
      id: "rel-pending",
      title: "Pending Release",
      version: "1.0.0",
      artifact_digest: "a".repeat(64),
      artifact_image: "ghcr.io/org/asdo:1.0.0",
      strategy: "canary",
      target_environment: "staging",
      status: "pending_approval",
    };

    render(
      <DeploymentDashboard
        plans={[pendingPlan]}
        selectedPlanId="rel-pending"
        onApproveDeploy={onApproveDeploy}
      />,
    );

    const approveBtn = screen.getByTestId("approve-deploy-btn");
    fireEvent.click(approveBtn);
    expect(onApproveDeploy).toHaveBeenCalledWith("rel-pending");
  });

  it("renders empty state when no plans exist", () => {
    render(<DeploymentDashboard plans={[]} />);
    expect(screen.getByText("Select a release plan to inspect details.")).toBeInTheDocument();
  });
});
