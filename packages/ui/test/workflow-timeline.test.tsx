import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { WorkflowCheckpoint, WorkflowExecution } from "@asdo/contracts";

import { WorkflowTimeline } from "../src/workflow-timeline";

describe("WorkflowTimeline component", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  const sampleExecution: WorkflowExecution = {
    id: "wf_101",
    requirement_id: "req_auth_01",
    plan_id: "plan_101",
    current_node: "awaiting_human_approval",
    state: "awaiting_approval",
    step_count: 3,
    actor_id: "usr_lead_1",
    created_at: timestamp,
    updated_at: timestamp,
  };

  const sampleCheckpoints: WorkflowCheckpoint[] = [
    {
      id: "chk_001",
      workflow_id: "wf_101",
      step_index: 0,
      node_name: "requirements_analysis",
      state_payload: {},
      created_at: timestamp,
    },
    {
      id: "chk_002",
      workflow_id: "wf_101",
      step_index: 1,
      node_name: "planning_and_budget",
      state_payload: {},
      created_at: timestamp,
    },
    {
      id: "chk_003",
      workflow_id: "wf_101",
      step_index: 2,
      node_name: "awaiting_human_approval",
      state_payload: {},
      created_at: timestamp,
    },
  ];

  it("renders workflow execution details, active lifecycle node, and checkpoints", () => {
    render(<WorkflowTimeline execution={sampleExecution} checkpoints={sampleCheckpoints} />);

    expect(screen.getByText("Durable Workflow Execution")).toBeVisible();
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("awaiting approval");
    expect(screen.getByTestId("timeline-node-awaiting_human_approval")).toBeVisible();
    expect(screen.getByTestId("checkpoint-row-chk_001")).toBeVisible();
    expect(screen.getByTestId("checkpoint-row-chk_002")).toBeVisible();
    expect(screen.getByTestId("checkpoint-row-chk_003")).toBeVisible();
  });

  it("handles approve and reject signals in awaiting_approval state", () => {
    const onSignal = vi.fn();
    render(
      <WorkflowTimeline
        execution={sampleExecution}
        checkpoints={sampleCheckpoints}
        onSignal={onSignal}
      />,
    );

    const approveBtn = screen.getByTestId("signal-approve-btn");
    fireEvent.click(approveBtn);
    expect(onSignal).toHaveBeenCalledWith("approve", { rationale: "Lead approval granted" });

    const rejectBtn = screen.getByTestId("signal-reject-btn");
    fireEvent.click(rejectBtn);
    expect(onSignal).toHaveBeenCalledWith("reject", { reason: "Requirements need revision" });
  });

  it("handles pause and resume signals", () => {
    const onSignal = vi.fn();
    const runningExecution: WorkflowExecution = {
      ...sampleExecution,
      state: "running",
      current_node: "execution_dispatch",
    };

    const { rerender } = render(
      <WorkflowTimeline
        execution={runningExecution}
        checkpoints={sampleCheckpoints}
        onSignal={onSignal}
      />,
    );

    const pauseBtn = screen.getByTestId("signal-interrupt-btn");
    fireEvent.click(pauseBtn);
    expect(onSignal).toHaveBeenCalledWith("interrupt");

    // Rerender as paused
    const pausedExecution: WorkflowExecution = {
      ...sampleExecution,
      state: "paused",
    };
    rerender(
      <WorkflowTimeline
        execution={pausedExecution}
        checkpoints={sampleCheckpoints}
        onSignal={onSignal}
      />,
    );

    const resumeBtn = screen.getByTestId("signal-resume-btn");
    fireEvent.click(resumeBtn);
    expect(onSignal).toHaveBeenCalledWith("resume");
  });

  it("handles checkpoint rollback action", () => {
    const onRollback = vi.fn();
    render(
      <WorkflowTimeline
        execution={sampleExecution}
        checkpoints={sampleCheckpoints}
        onRollback={onRollback}
      />,
    );

    const rollbackBtn = screen.getByTestId("rollback-btn-chk_001");
    fireEvent.click(rollbackBtn);
    expect(onRollback).toHaveBeenCalledWith("chk_001");
  });
});
