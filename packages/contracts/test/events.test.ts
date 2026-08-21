import { describe, expect, it } from "vitest";

import {
  streamConnectionStatusSchema,
  workflowEventFilterSchema,
  workflowEventSchema,
  workflowEventTypeSchema,
} from "../src/index";

describe("Event contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  it("validates workflow event schema", () => {
    const event = {
      id: "evt_001",
      workflow_id: "wf_101",
      event_type: "token_usage" as const,
      node_name: "execution_dispatch" as const,
      payload: { tokens_used: 1500, cost_usd: 0.05 },
      timestamp,
    };
    expect(workflowEventSchema.parse(event)).toEqual(event);
  });

  it("validates connection statuses", () => {
    expect(streamConnectionStatusSchema.parse("connected")).toBe("connected");
    expect(streamConnectionStatusSchema.parse("connecting")).toBe("connecting");
    expect(streamConnectionStatusSchema.parse("reconnecting")).toBe("reconnecting");
    expect(streamConnectionStatusSchema.parse("disconnected")).toBe("disconnected");
  });

  it("validates event filter schema", () => {
    const filter = {
      event_types: ["node_transition" as const, "token_usage" as const],
      search_query: "tokens",
      node_name: "planning_and_budget" as const,
    };
    expect(workflowEventFilterSchema.parse(filter)).toEqual(filter);
  });

  it("rejects invalid event types and stream statuses", () => {
    expect(() => workflowEventTypeSchema.parse("invalid_event")).toThrow();
    expect(() => streamConnectionStatusSchema.parse("invalid_status")).toThrow();
  });
});
