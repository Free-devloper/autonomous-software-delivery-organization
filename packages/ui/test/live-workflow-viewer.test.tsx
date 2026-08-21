import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { WorkflowCheckpoint, WorkflowEvent, WorkflowExecution } from "@asdo/contracts";
import { LiveWorkflowViewer } from "../src/index";

describe("LiveWorkflowViewer", () => {
  const execution: WorkflowExecution = {
    id: "wf-live-101",
    requirement_id: "req-101",
    plan_id: "plan-101",
    current_node: "planning_and_budget",
    state: "running",
    step_count: 1,
    actor_id: "usr-lead-1",
    created_at: "2026-08-20T12:00:00.000Z",
    updated_at: "2026-08-20T12:05:00.000Z",
  };

  const checkpoints: WorkflowCheckpoint[] = [
    {
      id: "chk-1",
      workflow_id: "wf-live-101",
      step_index: 0,
      node_name: "requirements_analysis",
      state_payload: { requirement_id: "req-101" },
      created_at: "2026-08-20T12:00:00.000Z",
    },
  ];

  const liveEvents: WorkflowEvent[] = [
    {
      id: "evt-1",
      workflow_id: "wf-live-101",
      event_type: "node_transition",
      node_name: "requirements_analysis",
      payload: { step: 0 },
      timestamp: "2026-08-20T12:00:00.000Z",
    },
    {
      id: "evt-2",
      workflow_id: "wf-live-101",
      event_type: "token_usage",
      node_name: "planning_and_budget",
      payload: { tokens_used: 1200, cost_usd: 0.04 },
      timestamp: "2026-08-20T12:01:00.000Z",
    },
  ];

  it("renders live metrics, connection status badge, and streamed events feed", () => {
    render(
      <LiveWorkflowViewer
        execution={execution}
        checkpoints={checkpoints}
        liveEvents={liveEvents}
        connectionStatus="connected"
      />,
    );

    expect(screen.getByTestId("live-workflow-viewer")).toBeInTheDocument();
    expect(screen.getByTestId("stream-connection-badge")).toHaveTextContent("connected");
    expect(screen.getByTestId("metric-tokens")).toHaveTextContent("1,200");
    expect(screen.getByTestId("metric-cost")).toHaveTextContent("$0.0400");
    expect(screen.getByTestId("metric-events-count")).toHaveTextContent("2");
    expect(screen.getByTestId("metric-active-node")).toHaveTextContent("planning_and_budget");
    expect(screen.getByTestId("event-item-evt-1")).toBeInTheDocument();
    expect(screen.getByTestId("event-item-evt-2")).toBeInTheDocument();
  });

  it("filters streamed events by event type and search query", () => {
    render(
      <LiveWorkflowViewer
        execution={execution}
        checkpoints={checkpoints}
        liveEvents={liveEvents}
        connectionStatus="connected"
      />,
    );

    // Filter by token_usage
    fireEvent.click(screen.getByTestId("filter-btn-token_usage"));
    expect(screen.queryByTestId("event-item-evt-1")).not.toBeInTheDocument();
    expect(screen.getByTestId("event-item-evt-2")).toBeInTheDocument();

    // Toggle filter back off
    fireEvent.click(screen.getByTestId("filter-btn-token_usage"));
    expect(screen.getByTestId("event-item-evt-1")).toBeInTheDocument();

    // Search query filter
    const searchInput = screen.getByTestId("event-search-input");
    fireEvent.change(searchInput, { target: { value: "step" } });
    expect(screen.getByTestId("event-item-evt-1")).toBeInTheDocument();
    expect(screen.queryByTestId("event-item-evt-2")).not.toBeInTheDocument();
  });

  it("triggers onReconnect callback when stream is disconnected", () => {
    const handleReconnect = vi.fn();
    render(
      <LiveWorkflowViewer
        execution={execution}
        checkpoints={checkpoints}
        liveEvents={liveEvents}
        connectionStatus="disconnected"
        onReconnect={handleReconnect}
      />,
    );

    expect(screen.getByTestId("stream-connection-badge")).toHaveTextContent("disconnected");
    const reconnectBtn = screen.getByTestId("reconnect-stream-btn");
    fireEvent.click(reconnectBtn);
    expect(handleReconnect).toHaveBeenCalledTimes(1);
  });
});
