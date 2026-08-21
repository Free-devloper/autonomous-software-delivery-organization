import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ArchitecturePlan } from "@asdo/contracts";

import { PlanViewer } from "../src/plan-viewer";

describe("PlanViewer component", () => {
  const samplePlan: ArchitecturePlan = {
    id: "plan_101",
    requirement_id: "req_01",
    revision_id: "rev_01",
    summary: "Decomposition of token auth into backend and test tasks",
    work_packages: [
      {
        id: "wp_1",
        requirement_id: "req_01",
        revision_id: "rev_01",
        title: "Backend Auth Service",
        description: "Validate RS256 signatures",
        target_files: ["services/api/src/auth.py"],
        acceptance_criteria_ids: ["ac_1"],
        dependencies: [],
        assigned_specialist: "backend",
        budget: {
          max_tokens: 25000,
          max_duration_seconds: 180,
          max_cost_usd: 1.0,
        },
        status: "pending",
        created_at: "2026-08-20T12:00:00.000Z",
      },
    ],
    edges: [],
    total_budget: {
      max_tokens: 25000,
      max_duration_seconds: 180,
      max_cost_usd: 1.0,
    },
    is_approved: false,
    created_at: "2026-08-20T12:00:00.000Z",
  };

  it("renders plan summary, budget metrics, and work package details", () => {
    render(<PlanViewer plan={samplePlan} />);

    expect(screen.getByText("Architecture Plan")).toBeVisible();
    expect(screen.getByTestId("plan-approval-badge")).toHaveTextContent("Pending Approval");
    expect(
      screen.getByText("Decomposition of token auth into backend and test tasks"),
    ).toBeVisible();
    expect(screen.getByTestId("budget-tokens")).toHaveTextContent("25,000");
    expect(screen.getByTestId("budget-duration")).toHaveTextContent("180s");
    expect(screen.getByTestId("budget-cost")).toHaveTextContent("$1.00");
    expect(screen.getByText("Backend Auth Service")).toBeVisible();
    expect(screen.getByText("backend")).toBeVisible();
  });

  it("handles plan approval form submission", () => {
    const onApprove = vi.fn();
    render(<PlanViewer plan={samplePlan} onApprovePlan={onApprove} />);

    const approveBtn = screen.getByTestId("approve-plan-btn");
    fireEvent.click(approveBtn);

    expect(screen.getByTestId("approval-form")).toBeVisible();
    const rationaleInput = screen.getByTestId("approval-rationale-input");
    fireEvent.change(rationaleInput, { target: { value: "Approved for execution" } });

    fireEvent.click(screen.getByTestId("confirm-approval-btn"));
    expect(onApprove).toHaveBeenCalledWith("plan_101", "Approved for execution");
  });

  it("displays approval banner when plan is approved", () => {
    const approvedPlan: ArchitecturePlan = {
      ...samplePlan,
      is_approved: true,
      approval_rationale: "Verified by lead architect",
      approved_by: "usr_lead_1",
    };

    render(<PlanViewer plan={approvedPlan} />);

    expect(screen.getByTestId("plan-approval-badge")).toHaveTextContent("Approved");
    expect(screen.getByTestId("approval-details")).toHaveTextContent(
      "Approved by usr_lead_1: Verified by lead architect",
    );
  });
});
