"use client";

import type { FC } from "react";

export interface SpecialistAssignmentDisplay {
  id: string;
  role: string;
  task_name: string;
  owned_files: string[];
  constraints: string[];
  status: "queued" | "in_progress" | "completed" | "blocked" | "rejected";
  output_summary: string;
}

export interface CoordinatorViewProps {
  pipelineTitle: string;
  requirementId: string;
  artifactDigest: string;
  status: "queued" | "in_progress" | "completed" | "blocked" | "rejected";
  assignments: SpecialistAssignmentDisplay[];
  onTriggerPipeline?: (() => void) | undefined;
}

const roleIcons: Record<string, string> = {
  coordinator: "🎯",
  analyst: "📋",
  architect: "🏗️",
  coder: "⚡",
  tester: "🧪",
  reviewer: "🔍",
  release_manager: "🚀",
};

export const CoordinatorView: FC<CoordinatorViewProps> = ({
  pipelineTitle,
  requirementId,
  artifactDigest,
  status,
  assignments,
  onTriggerPipeline,
}) => {
  return (
    <div className="space-y-6" data-testid="coordinator-view">
      {/* Pipeline Header */}
      <div className="flex flex-col items-start justify-between gap-4 rounded-xl border border-indigo-800/40 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 backdrop-blur sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">{pipelineTitle}</h2>
            <span className="rounded-full border border-emerald-700 bg-emerald-950/60 px-3 py-0.5 text-xs font-bold uppercase text-emerald-300">
              {status}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Requirement: <span className="font-mono text-indigo-400">{requirementId}</span> •
            Content Digest:{" "}
            <span className="font-mono text-emerald-400">
              {artifactDigest ? artifactDigest.slice(0, 16) + "..." : "none"}
            </span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => onTriggerPipeline?.()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-indigo-500 shadow-md shadow-indigo-950"
          data-testid="trigger-pipeline-btn"
        >
          Dispatch Specialists
        </button>
      </div>

      {/* Specialist Team Timeline */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Specialist Agent Orchestration (AGENTS.md)
        </h3>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {assignments.map((a, idx) => (
            <div
              key={a.id}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700"
              data-testid={`assignment-card-${a.role}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{roleIcons[a.role] ?? "🤖"}</span>
                  <div>
                    <h4 className="font-bold text-white text-sm capitalize">
                      {a.role.replace("_", " ")}
                    </h4>
                    <p className="text-xs text-slate-400">
                      Step {idx + 1}: {a.task_name}
                    </p>
                  </div>
                </div>
                <span className="rounded px-2 py-0.5 text-[10px] font-bold uppercase bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                  {a.status}
                </span>
              </div>

              {/* Owned Files & Constraints */}
              <div className="mt-4 space-y-2 border-t border-slate-800 pt-3 text-xs">
                {a.owned_files.length > 0 && (
                  <div>
                    <span className="text-slate-500">Owned Files: </span>
                    <span className="font-mono text-indigo-300">{a.owned_files.join(", ")}</span>
                  </div>
                )}
                {a.constraints.length > 0 && (
                  <div>
                    <span className="text-slate-500">Invariants: </span>
                    <span className="text-slate-300">{a.constraints.join(" • ")}</span>
                  </div>
                )}
                {a.output_summary && (
                  <div className="rounded bg-slate-950/60 p-2 text-slate-300 font-mono text-[11px]">
                    ✓ {a.output_summary}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
