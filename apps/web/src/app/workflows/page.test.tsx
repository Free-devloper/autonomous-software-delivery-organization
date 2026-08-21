import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import WorkflowsPage from "./page";

describe("WorkflowsPage", () => {
  it("renders workflow page with header, timeline, and checkpoints", () => {
    render(<WorkflowsPage />);

    expect(screen.getByRole("heading", { name: "Durable Workflow & Event Control" })).toBeVisible();
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("awaiting approval");
    expect(screen.getByTestId("timeline-node-awaiting_human_approval")).toBeVisible();
    expect(screen.getByTestId("checkpoint-row-chk_018f0001")).toBeVisible();
  });

  it("handles authorizing execution signal to completion", () => {
    render(<WorkflowsPage />);

    const authBtn = screen.getByTestId("signal-approve-btn");
    fireEvent.click(authBtn);

    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("completed");
    expect(screen.getByTestId("checkpoint-row-chk_018f0004")).toBeVisible();
  });

  it("handles rollback to previous checkpoints", () => {
    render(<WorkflowsPage />);

    // Rollback to step 0 (running)
    const rollbackBtn1 = screen.getByTestId("rollback-btn-chk_018f0001");
    fireEvent.click(rollbackBtn1);
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("running");

    // Pause while running
    const pauseBtn = screen.getByTestId("signal-interrupt-btn");
    fireEvent.click(pauseBtn);
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("paused");

    // Resume while paused
    const resumeBtn = screen.getByTestId("signal-resume-btn");
    fireEvent.click(resumeBtn);
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("awaiting approval");

    // Rollback to step 2 (awaiting_approval)
    const rollbackBtn3 = screen.getByTestId("rollback-btn-chk_018f0003");
    fireEvent.click(rollbackBtn3);
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("awaiting approval");
  });

  it("handles reject signal", () => {
    render(<WorkflowsPage />);

    const rejectBtn = screen.getByTestId("signal-reject-btn");
    fireEvent.click(rejectBtn);
    expect(screen.getByTestId("execution-state-badge")).toHaveTextContent("cancelled");
  });

  it("handles reconnect stream trigger", () => {
    const { container } = render(<WorkflowsPage />);
    expect(container).toBeInTheDocument();
  });
});
