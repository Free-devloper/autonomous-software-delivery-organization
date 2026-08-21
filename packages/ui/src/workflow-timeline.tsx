"use client";

import type { WorkflowCheckpoint, WorkflowExecution, WorkflowNode } from "@asdo/contracts";

export interface WorkflowTimelineProps {
  execution: WorkflowExecution;
  checkpoints: WorkflowCheckpoint[];
  onSignal?: ((signalName: string, payload?: Record<string, unknown>) => void) | undefined;
  onRollback?: ((checkpointId: string) => void) | undefined;
}

const NODES_ORDER: { node: WorkflowNode; label: string }[] = [
  { node: "requirements_analysis", label: "Requirements Analysis" },
  { node: "planning_and_budget", label: "Planning & Budget" },
  { node: "awaiting_human_approval", label: "Human Approval Gate" },
  { node: "execution_dispatch", label: "Execution Dispatch" },
  { node: "verification_and_testing", label: "Verification & Testing" },
  { node: "review_and_signoff", label: "Review & Signoff" },
];

export function WorkflowTimeline({
  execution,
  checkpoints,
  onSignal,
  onRollback,
}: WorkflowTimelineProps) {
  const currentIndex = NODES_ORDER.findIndex((n) => n.node === execution.current_node);

  return (
    <div
      data-testid="workflow-timeline"
      className="flex flex-col gap-6 rounded-xl border border-slate-800 bg-slate-900/90 p-6 text-slate-100 shadow-xl backdrop-blur"
    >
      {/* Execution Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-100">Durable Workflow Execution</h2>
            <span
              data-testid="execution-state-badge"
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                execution.state === "completed"
                  ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                  : execution.state === "awaiting_approval"
                    ? "bg-amber-950/80 text-amber-400 border border-amber-800 animate-pulse"
                    : execution.state === "paused"
                      ? "bg-indigo-950/80 text-indigo-400 border border-indigo-800"
                      : execution.state === "cancelled"
                        ? "bg-rose-950/80 text-rose-400 border border-rose-800"
                        : "bg-blue-950/80 text-blue-400 border border-blue-800"
              }`}
            >
              {execution.state.replace("_", " ")}
            </span>
          </div>
          <p className="mt-1 text-xs font-mono text-slate-500">
            ID: {execution.id} | Requirement: {execution.requirement_id}
          </p>
        </div>

        {/* Action Signal Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {execution.state === "awaiting_approval" && onSignal && (
            <>
              <button
                data-testid="signal-approve-btn"
                onClick={() => {
                  onSignal("approve", { rationale: "Lead approval granted" });
                }}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition"
              >
                Authorize Execution
              </button>
              <button
                data-testid="signal-reject-btn"
                onClick={() => {
                  onSignal("reject", { reason: "Requirements need revision" });
                }}
                className="rounded-lg bg-rose-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-600 transition"
              >
                Reject
              </button>
            </>
          )}

          {execution.state === "running" && onSignal && (
            <button
              data-testid="signal-interrupt-btn"
              onClick={() => {
                onSignal("interrupt");
              }}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-500 transition"
            >
              Pause Run
            </button>
          )}

          {execution.state === "paused" && onSignal && (
            <button
              data-testid="signal-resume-btn"
              onClick={() => {
                onSignal("resume");
              }}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 transition"
            >
              Resume Run
            </button>
          )}
        </div>
      </div>

      {/* Lifecycle Node Timeline */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Execution Lifecycle
        </h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {NODES_ORDER.map((item, idx) => {
            const isPast = idx < currentIndex;
            const isCurrent = idx === currentIndex;
            return (
              <div
                key={item.node}
                data-testid={`timeline-node-${item.node}`}
                className={`flex flex-col rounded-lg border p-3 text-xs transition ${
                  isCurrent
                    ? "border-indigo-500 bg-indigo-950/40 text-indigo-200 ring-1 ring-indigo-500"
                    : isPast
                      ? "border-emerald-900 bg-emerald-950/20 text-emerald-300"
                      : "border-slate-800 bg-slate-950/40 text-slate-500"
                }`}
              >
                <span className="text-[10px] font-mono text-slate-500">Step {idx + 1}</span>
                <span className="font-semibold">{item.label}</span>
                <span className="mt-1 text-[10px] uppercase">
                  {isCurrent ? "Active" : isPast ? "Completed" : "Pending"}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Persisted State Checkpoints with Rollback */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            State Checkpoints ({checkpoints.length})
          </h3>
          <span className="text-[11px] text-slate-500">Persisted in PostgreSQL</span>
        </div>

        <div className="flex flex-col gap-2">
          {checkpoints.map((chk) => (
            <div
              key={chk.id}
              data-testid={`checkpoint-row-${chk.id}`}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-indigo-400">#{chk.step_index}</span>
                <div>
                  <div className="font-semibold text-slate-200">{chk.node_name}</div>
                  <div className="text-[10px] font-mono text-slate-500">{chk.id}</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[10px] text-slate-500">
                  {new Date(chk.created_at).toLocaleTimeString()}
                </span>
                {onRollback && (
                  <button
                    data-testid={`rollback-btn-${chk.id}`}
                    onClick={() => {
                      onRollback(chk.id);
                    }}
                    className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 hover:border-slate-500 hover:text-white transition"
                  >
                    Rollback
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
