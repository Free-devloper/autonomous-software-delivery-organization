"use client";

import { useState } from "react";
import type {
  StreamConnectionStatus,
  WorkflowCheckpoint,
  WorkflowEvent,
  WorkflowExecution,
} from "@asdo/contracts";
import { LiveWorkflowViewer } from "@asdo/ui";

const defaultExecution: WorkflowExecution = {
  id: "wf_exec_018f0001",
  requirement_id: "req_auth_01",
  plan_id: "plan_auth_018f",
  current_node: "awaiting_human_approval",
  state: "awaiting_approval",
  step_count: 3,
  actor_id: "usr_lead_architect",
  created_at: "2026-08-20T00:00:00.000Z",
  updated_at: "2026-08-20T00:02:00.000Z",
};

const defaultCheckpoints: WorkflowCheckpoint[] = [
  {
    id: "chk_018f0001",
    workflow_id: "wf_exec_018f0001",
    step_index: 0,
    node_name: "requirements_analysis",
    state_payload: { requirement_id: "req_auth_01", criteria_count: 3 },
    created_at: "2026-08-20T00:00:00.000Z",
  },
  {
    id: "chk_018f0002",
    workflow_id: "wf_exec_018f0001",
    step_index: 1,
    node_name: "planning_and_budget",
    state_payload: { plan_id: "plan_auth_018f", total_tokens: 50000 },
    created_at: "2026-08-20T00:01:00.000Z",
  },
  {
    id: "chk_018f0003",
    workflow_id: "wf_exec_018f0001",
    step_index: 2,
    node_name: "awaiting_human_approval",
    state_payload: { awaiting_token_budget_auth: true },
    created_at: "2026-08-20T00:02:00.000Z",
  },
];

const defaultLiveEvents: WorkflowEvent[] = [
  {
    id: "evt_001",
    workflow_id: "wf_exec_018f0001",
    event_type: "node_transition",
    node_name: "requirements_analysis",
    payload: { step: 0, status: "started" },
    timestamp: "2026-08-20T00:00:00.000Z",
  },
  {
    id: "evt_002",
    workflow_id: "wf_exec_018f0001",
    event_type: "token_usage",
    node_name: "planning_and_budget",
    payload: { tokens_used: 18500, cost_usd: 0.055 },
    timestamp: "2026-08-20T00:01:00.000Z",
  },
  {
    id: "evt_003",
    workflow_id: "wf_exec_018f0001",
    event_type: "approval_requested",
    node_name: "awaiting_human_approval",
    payload: { gate: "lead_authorization_required" },
    timestamp: "2026-08-20T00:02:00.000Z",
  },
];

export default function WorkflowsPage() {
  const [execution, setExecution] = useState<WorkflowExecution>(defaultExecution);
  const [checkpoints, setCheckpoints] = useState<WorkflowCheckpoint[]>(defaultCheckpoints);
  const [liveEvents, setLiveEvents] = useState<WorkflowEvent[]>(defaultLiveEvents);
  const [connectionStatus, setConnectionStatus] = useState<StreamConnectionStatus>("connected");

  const handleSignal = (signalName: string) => {
    const now = new Date().toISOString();
    switch (signalName) {
      case "approve": {
        const newChk: WorkflowCheckpoint = {
          id: `chk_018f000${(checkpoints.length + 1).toString()}`,
          workflow_id: execution.id,
          step_index: checkpoints.length,
          node_name: "review_and_signoff",
          state_payload: { completed: true },
          created_at: now,
        };
        const newEvt: WorkflowEvent = {
          id: `evt_00${(liveEvents.length + 1).toString()}`,
          workflow_id: execution.id,
          event_type: "status_change",
          node_name: "review_and_signoff",
          payload: { action: "approved", new_state: "completed" },
          timestamp: now,
        };
        setCheckpoints((prev) => [...prev, newChk]);
        setLiveEvents((prev) => [...prev, newEvt]);
        setExecution((prev) => ({
          ...prev,
          state: "completed",
          current_node: "review_and_signoff",
          step_count: prev.step_count + 1,
          updated_at: now,
        }));
        break;
      }
      case "reject":
        setExecution((prev) => ({ ...prev, state: "cancelled" }));
        break;
      case "interrupt":
        setExecution((prev) => ({ ...prev, state: "paused" }));
        break;
      case "resume":
        setExecution((prev) => ({ ...prev, state: "awaiting_approval" }));
        break;
    }
  };

  const handleRollback = (checkpointId: string) => {
    const target = checkpoints.find((c) => c.id === checkpointId);
    if (target) {
      setExecution((prev) => ({
        ...prev,
        current_node: target.node_name,
        step_count: target.step_index + 1,
        state: target.node_name === "awaiting_human_approval" ? "awaiting_approval" : "running",
      }));
    }
  };

  const handleReconnect = () => {
    setConnectionStatus("connecting");
    setTimeout(() => {
      setConnectionStatus("connected");
    }, 500);
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Durable Workflow & Event Control
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Temporal orchestration, live Server-Sent Events stream, token/cost telemetry, and
              zero-cost human approval gates.
            </p>
          </div>
        </header>

        <LiveWorkflowViewer
          execution={execution}
          checkpoints={checkpoints}
          liveEvents={liveEvents}
          connectionStatus={connectionStatus}
          onSignal={handleSignal}
          onRollback={handleRollback}
          onReconnect={handleReconnect}
        />
      </div>
    </main>
  );
}
