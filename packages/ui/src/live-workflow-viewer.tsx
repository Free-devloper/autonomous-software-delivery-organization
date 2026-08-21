"use client";

import { useMemo, useState } from "react";
import type {
  StreamConnectionStatus,
  WorkflowCheckpoint,
  WorkflowEvent,
  WorkflowExecution,
} from "@asdo/contracts";
import { WorkflowTimeline } from "./workflow-timeline";

export interface LiveWorkflowViewerProps {
  execution: WorkflowExecution;
  checkpoints: WorkflowCheckpoint[];
  liveEvents: WorkflowEvent[];
  connectionStatus: StreamConnectionStatus;
  onSignal?: ((signalName: string, payload?: Record<string, unknown>) => void) | undefined;
  onRollback?: ((checkpointId: string) => void) | undefined;
  onReconnect?: (() => void) | undefined;
}

const EVENT_TYPES: { type: string; label: string }[] = [
  { type: "node_transition", label: "Node Transitions" },
  { type: "token_usage", label: "Token Usage" },
  { type: "agent_message", label: "Agent Messages" },
  { type: "approval_requested", label: "Approvals" },
  { type: "status_change", label: "Status Changes" },
];

export function LiveWorkflowViewer({
  execution,
  checkpoints,
  liveEvents,
  connectionStatus,
  onSignal,
  onRollback,
  onReconnect,
}: LiveWorkflowViewerProps) {
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEvents = useMemo(() => {
    return liveEvents.filter((evt) => {
      if (selectedTypes.length > 0 && !selectedTypes.includes(evt.event_type)) {
        return false;
      }
      if (searchQuery.trim() !== "") {
        const query = searchQuery.toLowerCase();
        const payloadStr = JSON.stringify(evt.payload).toLowerCase();
        const matchesType = evt.event_type.toLowerCase().includes(query);
        const matchesNode = evt.node_name.toLowerCase().includes(query);
        if (!matchesType && !matchesNode && !payloadStr.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [liveEvents, selectedTypes, searchQuery]);

  const metrics = useMemo(() => {
    let totalTokens = 0;
    let totalCostUsd = 0;
    for (const evt of liveEvents) {
      if (evt.event_type === "token_usage") {
        const payload = evt.payload;
        const tokens =
          typeof payload.tokens_used === "number"
            ? payload.tokens_used
            : typeof payload.tokens === "number"
              ? payload.tokens
              : 0;
        const cost = typeof payload.cost_usd === "number" ? payload.cost_usd : 0;
        totalTokens += tokens;
        totalCostUsd += cost;
      }
    }
    return { totalTokens, totalCostUsd };
  }, [liveEvents]);

  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  };

  return (
    <div
      data-testid="live-workflow-viewer"
      className="flex flex-col gap-6 rounded-2xl border border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-2xl"
    >
      {/* Stream Header & Status Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-3 w-3 items-center justify-center">
            <span
              className={`h-3 w-3 rounded-full ${
                connectionStatus === "connected"
                  ? "bg-emerald-400 animate-pulse"
                  : connectionStatus === "connecting" || connectionStatus === "reconnecting"
                    ? "bg-amber-400 animate-ping"
                    : "bg-rose-500"
              }`}
            />
          </div>
          <h2 className="text-lg font-bold text-slate-100">Live SSE Event Stream</h2>
          <span
            data-testid="stream-connection-badge"
            className={`rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wider ${
              connectionStatus === "connected"
                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                : connectionStatus === "reconnecting"
                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                  : "bg-slate-900 text-slate-400 border border-slate-800"
            }`}
          >
            {connectionStatus}
          </span>
        </div>

        {connectionStatus === "disconnected" && onReconnect && (
          <button
            data-testid="reconnect-stream-btn"
            onClick={onReconnect}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:border-slate-500 hover:bg-slate-800 transition"
          >
            Reconnect Stream
          </button>
        )}
      </div>

      {/* Resource Metrics Bar */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Total Tokens Consumed
          </span>
          <div data-testid="metric-tokens" className="mt-1 text-2xl font-bold text-indigo-400">
            {metrics.totalTokens.toLocaleString()}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Estimated Cost (USD)
          </span>
          <div data-testid="metric-cost" className="mt-1 text-2xl font-bold text-emerald-400">
            ${metrics.totalCostUsd.toFixed(4)}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Events Streamed
          </span>
          <div data-testid="metric-events-count" className="mt-1 text-2xl font-bold text-sky-400">
            {liveEvents.length}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Active Node
          </span>
          <div
            data-testid="metric-active-node"
            className="mt-1 text-sm font-semibold text-slate-200 truncate"
          >
            {execution.current_node}
          </div>
        </div>
      </div>

      {/* Durable Timeline */}
      <WorkflowTimeline
        execution={execution}
        checkpoints={checkpoints}
        onSignal={onSignal}
        onRollback={onRollback}
      />

      {/* Live Event Feed & Controls */}
      <div className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-900/90 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h3 className="text-sm font-bold text-slate-200">
            Stream Event History ({filteredEvents.length})
          </h3>

          <input
            data-testid="event-search-input"
            type="text"
            placeholder="Search events payload..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
            }}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        {/* Filter Badges */}
        <div className="flex flex-wrap gap-2">
          {EVENT_TYPES.map((et) => {
            const isSelected = selectedTypes.includes(et.type);
            return (
              <button
                key={et.type}
                data-testid={`filter-btn-${et.type}`}
                onClick={() => {
                  toggleTypeFilter(et.type);
                }}
                className={`rounded-full px-3 py-1 text-[11px] font-medium transition ${
                  isSelected
                    ? "bg-indigo-600 text-white"
                    : "border border-slate-700 bg-slate-950 text-slate-400 hover:border-slate-500"
                }`}
              >
                {et.label}
              </button>
            );
          })}
        </div>

        {/* Event List */}
        <div
          data-testid="events-feed-list"
          className="flex max-h-80 flex-col gap-2 overflow-y-auto pr-1"
        >
          {filteredEvents.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-800 p-8 text-center text-xs text-slate-500">
              No matching live events streamed yet.
            </div>
          ) : (
            filteredEvents.map((evt) => (
              <div
                key={evt.id}
                data-testid={`event-item-${evt.id}`}
                className="flex flex-col gap-1.5 rounded-lg border border-slate-800 bg-slate-950/80 p-3 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-indigo-400">{evt.id}</span>
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
                      {evt.event_type}
                    </span>
                    <span className="text-[11px] text-slate-400">{evt.node_name}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <pre className="overflow-x-auto rounded bg-slate-900 p-2 font-mono text-[11px] text-slate-300">
                  {JSON.stringify(evt.payload, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
