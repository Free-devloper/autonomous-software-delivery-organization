import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CoordinatorView, type SpecialistAssignmentDisplay } from "../src/coordinator-view";

describe("CoordinatorView", () => {
  const mockAssignments: SpecialistAssignmentDisplay[] = [
    {
      id: "asgn-1",
      role: "analyst",
      task_name: "Decompose requirements",
      owned_files: ["docs/requirements/"],
      constraints: ["Strict trace links"],
      status: "completed",
      output_summary: "Acceptance criteria generated",
    },
    {
      id: "asgn-2",
      role: "coder",
      task_name: "Implement patch",
      owned_files: [],
      constraints: [],
      status: "in_progress",
      output_summary: "",
    },
  ];

  it("renders pipeline title, status and specialist cards", () => {
    render(
      <CoordinatorView
        pipelineTitle="Deliver Auth System"
        requirementId="req-001"
        artifactDigest={"a".repeat(64)}
        status="completed"
        assignments={mockAssignments}
      />,
    );

    expect(screen.getByTestId("coordinator-view")).toBeInTheDocument();
    expect(screen.getByText("Deliver Auth System")).toBeInTheDocument();
    expect(screen.getByText("Step 1: Decompose requirements")).toBeInTheDocument();
    expect(screen.getByText("Step 2: Implement patch")).toBeInTheDocument();
  });

  it("renders fallback when digest is empty", () => {
    render(
      <CoordinatorView
        pipelineTitle="Deliver Auth System"
        requirementId="req-001"
        artifactDigest=""
        status="queued"
        assignments={mockAssignments}
      />,
    );
    expect(screen.getByText("none")).toBeInTheDocument();
  });

  it("triggers pipeline dispatch callback", () => {
    const onTrigger = vi.fn();
    render(
      <CoordinatorView
        pipelineTitle="Deliver Auth System"
        requirementId="req-001"
        artifactDigest={"a".repeat(64)}
        status="completed"
        assignments={mockAssignments}
        onTriggerPipeline={onTrigger}
      />,
    );

    const btn = screen.getByTestId("trigger-pipeline-btn");
    fireEvent.click(btn);
    expect(onTrigger).toHaveBeenCalledTimes(1);
  });
});
