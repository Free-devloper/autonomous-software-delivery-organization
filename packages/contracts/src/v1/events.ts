import { z } from "zod";
import { workflowNodeSchema } from "./workflow";

/** Category of live events emitted during workflow execution. */
export const workflowEventTypeSchema = z.enum([
  "node_transition",
  "token_usage",
  "agent_message",
  "approval_requested",
  "status_change",
]);
export type WorkflowEventType = z.infer<typeof workflowEventTypeSchema>;

/** Individual event payload transmitted over Server-Sent Events (SSE). */
export const workflowEventSchema = z
  .object({
    id: z.string().min(1),
    workflow_id: z.string().min(1),
    event_type: workflowEventTypeSchema,
    node_name: workflowNodeSchema,
    payload: z.record(z.string(), z.unknown()).default({}),
    timestamp: z.iso.datetime(),
  })
  .strict();
export type WorkflowEvent = z.infer<typeof workflowEventSchema>;

/** Stream connection status for UI subscribers. */
export const streamConnectionStatusSchema = z.enum([
  "connecting",
  "connected",
  "reconnecting",
  "disconnected",
]);
export type StreamConnectionStatus = z.infer<typeof streamConnectionStatusSchema>;

/** Filter settings for live event stream rendering in the UI. */
export const workflowEventFilterSchema = z
  .object({
    event_types: z.array(workflowEventTypeSchema).optional(),
    search_query: z.string().optional(),
    node_name: workflowNodeSchema.optional(),
  })
  .strict();
export type WorkflowEventFilter = z.infer<typeof workflowEventFilterSchema>;
