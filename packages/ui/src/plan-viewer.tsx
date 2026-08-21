"use client";

import { useState } from "react";
import type { ArchitecturePlan } from "@asdo/contracts";

export interface PlanViewerProps {
  plan: ArchitecturePlan;
  onApprovePlan?: (planId: string, rationale: string) => void;
}

export function PlanViewer({ plan, onApprovePlan }: PlanViewerProps) {
  const [rationale, setRationale] = useState("");
  const [isApproving, setIsApproving] = useState(false);

  const handleApprove = () => {
    if (onApprovePlan && rationale.trim()) {
      onApprovePlan(plan.id, rationale);
      setIsApproving(false);
    }
  };

  return (
    <div
      data-testid="plan-viewer"
      className="flex flex-col gap-6 rounded-xl border border-slate-800 bg-slate-900/90 p-6 text-slate-100 shadow-xl backdrop-blur"
    >
      {/* Header with Summary and Approval Badge */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-100">Architecture Plan</h2>
            <span
              data-testid="plan-approval-badge"
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                plan.is_approved
                  ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                  : "bg-amber-950/80 text-amber-400 border border-amber-800"
              }`}
            >
              {plan.is_approved ? "Approved" : "Pending Approval"}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">{plan.summary}</p>
        </div>

        {!plan.is_approved && onApprovePlan && (
          <button
            data-testid="approve-plan-btn"
            onClick={() => {
              setIsApproving(!isApproving);
            }}
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-emerald-500"
          >
            {isApproving ? "Cancel" : "Approve Plan"}
          </button>
        )}
      </div>

      {/* Approval Form */}
      {isApproving && (
        <div
          data-testid="approval-form"
          className="flex flex-col gap-3 rounded-lg border border-emerald-900/60 bg-emerald-950/20 p-4"
        >
          <h3 className="text-sm font-semibold text-emerald-300">Authorize Execution Plan</h3>
          <p className="text-xs text-slate-400">
            Confirming approval authorizes automated workflow dispatch within allocated budgets.
          </p>
          <textarea
            data-testid="approval-rationale-input"
            value={rationale}
            onChange={(e) => {
              setRationale(e.target.value);
            }}
            placeholder="Approval rationale (e.g. Verified against SRS requirements)"
            rows={2}
            className="rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <button
            data-testid="confirm-approval-btn"
            onClick={handleApprove}
            className="self-start rounded bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            Confirm Approval
          </button>
        </div>
      )}

      {/* Approval Details Banner */}
      {plan.is_approved && plan.approval_rationale && (
        <div
          data-testid="approval-details"
          className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-3 text-xs text-emerald-300"
        >
          <span className="font-semibold">Approved by {plan.approved_by ?? "Platform Lead"}:</span>{" "}
          {plan.approval_rationale}
        </div>
      )}

      {/* Total Budget Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs font-medium uppercase text-slate-400">Token Budget</div>
          <div data-testid="budget-tokens" className="mt-1 text-lg font-bold text-indigo-400">
            {plan.total_budget.max_tokens.toLocaleString()}
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs font-medium uppercase text-slate-400">Max Duration</div>
          <div data-testid="budget-duration" className="mt-1 text-lg font-bold text-amber-400">
            {plan.total_budget.max_duration_seconds}s
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <div className="text-xs font-medium uppercase text-slate-400">Estimated Cost</div>
          <div data-testid="budget-cost" className="mt-1 text-lg font-bold text-emerald-400">
            ${plan.total_budget.max_cost_usd.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Work Packages List */}
      <div className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Work Packages ({plan.work_packages.length})
        </h3>
        <div className="flex flex-col gap-3">
          {plan.work_packages.map((wp) => (
            <div
              key={wp.id}
              data-testid={`work-package-${wp.id}`}
              className="flex flex-col gap-2 rounded-lg border border-slate-800 bg-slate-950/70 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-slate-200">{wp.title}</h4>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      wp.assigned_specialist === "backend"
                        ? "bg-blue-950 text-blue-400 border border-blue-800"
                        : wp.assigned_specialist === "frontend"
                          ? "bg-purple-950 text-purple-400 border border-purple-800"
                          : wp.assigned_specialist === "testing"
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : "bg-amber-950 text-amber-400 border border-amber-800"
                    }`}
                  >
                    {wp.assigned_specialist}
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-500">{wp.id}</span>
              </div>
              <p className="text-xs text-slate-400">{wp.description}</p>
              <div className="mt-1 flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
                <div>
                  <span className="text-slate-500">Files:</span> {wp.target_files.join(", ")}
                </div>
                {wp.dependencies.length > 0 && (
                  <div>
                    <span className="text-slate-500">Depends on:</span> {wp.dependencies.join(", ")}
                  </div>
                )}
                <div>
                  <span className="text-slate-500">Budget:</span>{" "}
                  {wp.budget.max_tokens.toLocaleString()} tokens / ${wp.budget.max_cost_usd}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
