import { z } from "zod";

/** Execution status of a durable workflow run. */
export const workflowStateSchema = z.enum([
  "pending",
  "running",
  "awaiting_approval",
  "paused",
  "completed",
  "failed",
  "cancelled",
]);
export type WorkflowState = z.infer<typeof workflowStateSchema>;

/** Standard lifecycle nodes in the autonomous software delivery workflow. */
export const workflowNodeSchema = z.enum([
  "requirements_analysis",
  "planning_and_budget",
  "awaiting_human_approval",
  "execution_dispatch",
  "verification_and_testing",
  "review_and_signoff",
]);
export type WorkflowNode = z.infer<typeof workflowNodeSchema>;

/** Persisted state checkpoint for durable execution replay and rollback. */
export const workflowCheckpointSchema = z
  .object({
    id: z.string().min(1),
    workflow_id: z.string().min(1),
    step_index: z.number().int().nonnegative(),
    node_name: workflowNodeSchema,
    state_payload: z.record(z.string(), z.unknown()),
    created_at: z.iso.datetime(),
  })
  .strict();
export type WorkflowCheckpoint = z.infer<typeof workflowCheckpointSchema>;

/** Durable workflow execution instance with active state and checkpoints. */
export const workflowExecutionSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    plan_id: z.string().optional(),
    current_node: workflowNodeSchema,
    state: workflowStateSchema,
    step_count: z.number().int().nonnegative(),
    actor_id: z.string().min(1),
    created_at: z.iso.datetime(),
    updated_at: z.iso.datetime(),
  })
  .strict();
export type WorkflowExecution = z.infer<typeof workflowExecutionSchema>;

/** Request payload to start a new durable workflow run. */
export const startWorkflowRequestSchema = z
  .object({
    requirement_id: z.string().min(1),
    plan_id: z.string().optional(),
    initial_payload: z.record(z.string(), z.unknown()).default({}),
  })
  .strict();
export type StartWorkflowRequest = z.infer<typeof startWorkflowRequestSchema>;

/** Signal payload sent to a running or awaiting workflow. */
export const signalWorkflowRequestSchema = z
  .object({
    signal_name: z.enum(["approve", "reject", "interrupt", "resume"]),
    payload: z.record(z.string(), z.unknown()).default({}),
  })
  .strict();
export type SignalWorkflowRequest = z.infer<typeof signalWorkflowRequestSchema>;
