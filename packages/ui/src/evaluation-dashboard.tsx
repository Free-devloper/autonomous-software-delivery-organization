"use client";

import type { FC } from "react";

export interface MetricItemDisplay {
  name: string;
  category: string;
  score: number;
  target_threshold: number;
  passed: boolean;
  unit: string;
  details?: string;
}

export interface EvaluationDashboardProps {
  status: "running" | "passed" | "warning" | "failed";
  summary: string;
  metrics: MetricItemDisplay[];
  totalCostUsd: number;
  budgetLimitUsd: number;
  budgetConsumedPercentage: number;
  isWithinBudget: boolean;
  rpoMinutes: number;
  rtoMinutes: number;
  lastBackupDigest?: string;
  onRunEvaluation?: (() => void) | undefined;
  onTriggerBackup?: (() => void) | undefined;
}

export const EvaluationDashboard: FC<EvaluationDashboardProps> = ({
  status,
  summary,
  metrics,
  totalCostUsd,
  budgetLimitUsd,
  budgetConsumedPercentage,
  isWithinBudget,
  rpoMinutes,
  rtoMinutes,
  lastBackupDigest,
  onRunEvaluation,
  onTriggerBackup,
}) => {
  const passedCount = metrics.filter((m) => m.passed).length;

  return (
    <div className="space-y-6" data-testid="evaluation-dashboard">
      {/* Production Readiness Banner */}
      <div className="flex flex-col items-start justify-between gap-4 rounded-xl border border-indigo-800/40 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 backdrop-blur sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">Production Readiness &amp; Evaluation</h2>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                status === "passed"
                  ? "border border-emerald-700 bg-emerald-950/60 text-emerald-300"
                  : "border border-amber-700 bg-amber-950/60 text-amber-300"
              }`}
            >
              {status}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">{summary}</p>
        </div>
        <button
          type="button"
          onClick={() => onRunEvaluation?.()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-indigo-500 shadow-md shadow-indigo-950"
          data-testid="run-evaluation-btn"
        >
          Run Holistic Evaluation
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Quality & Readiness Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Readiness Scorecard
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">{passedCount}</span>
            <span className="text-sm text-slate-400">/ {metrics.length} thresholds satisfied</span>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full bg-emerald-500"
              style={{
                width: `${String(metrics.length > 0 ? (passedCount / metrics.length) * 100 : 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Cost & Quota Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Model Cost &amp; Quota
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-indigo-400">${totalCostUsd.toFixed(2)}</span>
            <span className="text-sm text-slate-400">/ ${budgetLimitUsd.toFixed(2)} budget</span>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className={`h-full ${isWithinBudget ? "bg-indigo-500" : "bg-rose-500"}`}
              style={{ width: `${String(Math.min(budgetConsumedPercentage, 100))}%` }}
            />
          </div>
        </div>

        {/* DR / Backup Readiness Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Disaster Recovery
            </p>
            <button
              type="button"
              onClick={() => onTriggerBackup?.()}
              className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 underline"
            >
              Trigger Snapshot
            </button>
          </div>
          <div className="mt-2 flex items-center gap-4">
            <div>
              <p className="text-[10px] text-slate-500 uppercase">RPO Target</p>
              <p className="text-base font-bold text-white">{rpoMinutes}m</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">RTO Target</p>
              <p className="text-base font-bold text-white">{rtoMinutes}m</p>
            </div>
          </div>
          {lastBackupDigest && (
            <p className="mt-2 font-mono text-[10px] text-slate-500 truncate">
              Digest: {lastBackupDigest.slice(0, 16)}...
            </p>
          )}
        </div>
      </div>

      {/* Detailed Criteria Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Evaluation Criteria
        </h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((m) => (
            <div
              key={m.name}
              className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition hover:border-slate-700"
              data-testid={`metric-card-${m.name}`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-semibold text-white text-sm capitalize">
                    {m.name.replace(/_/g, " ")}
                  </h4>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                      m.passed
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                        : "bg-rose-950/60 text-rose-300 border border-rose-800/40"
                    }`}
                  >
                    {m.passed ? "Passed" : "Failed"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  {m.details ?? `Category: ${m.category}`}
                </p>
              </div>
              <div className="mt-4 flex items-baseline justify-between border-t border-slate-800 pt-2 text-xs">
                <span className="text-slate-500">
                  Target: {m.target_threshold} {m.unit}
                </span>
                <span className="font-mono font-bold text-white">
                  Actual: {m.score} {m.unit}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
