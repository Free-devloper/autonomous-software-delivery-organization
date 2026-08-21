import { describe, expect, it } from "vitest";

import {
  signalWorkflowRequestSchema,
  startWorkflowRequestSchema,
  workflowCheckpointSchema,
  workflowExecutionSchema,
  workflowNodeSchema,
  workflowStateSchema,
} from "../src/index";

describe("Workflow contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  it("validates workflow checkpoint schema", () => {
    const checkpoint = {
      id: "chk_001",
      workflow_id: "wf_101",
      step_index: 2,
      node_name: "planning_and_budget" as const,
      state_payload: { plan_id: "plan_101", verified: true },
      created_at: timestamp,
    };
    expect(workflowCheckpointSchema.parse(checkpoint)).toEqual(checkpoint);
  });

  it("validates workflow execution schema", () => {
    const execution = {
      id: "wf_101",
      requirement_id: "req_01",
      plan_id: "plan_101",
      current_node: "awaiting_human_approval" as const,
      state: "awaiting_approval" as const,
      step_count: 3,
      actor_id: "usr_lead_1",
      created_at: timestamp,
      updated_at: timestamp,
    };
    expect(workflowExecutionSchema.parse(execution)).toEqual(execution);
  });

  it("validates start and signal request schemas", () => {
    const startPayload = {
      requirement_id: "req_01",
      plan_id: "plan_101",
      initial_payload: { target_branch: "feature/auth" },
    };
    expect(startWorkflowRequestSchema.parse(startPayload)).toEqual(startPayload);

    const signalPayload = {
      signal_name: "approve" as const,
      payload: { rationale: "Approved by lead architect" },
    };
    expect(signalWorkflowRequestSchema.parse(signalPayload)).toEqual(signalPayload);
  });

  it("rejects invalid nodes and states", () => {
    expect(() => workflowNodeSchema.parse("invalid_node")).toThrow();
    expect(() => workflowStateSchema.parse("invalid_state")).toThrow();
  });
});
