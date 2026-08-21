"use client";

import type { FC } from "react";

export interface ReleasePlanDisplay {
  id: string;
  title: string;
  version: string;
  artifact_digest: string;
  artifact_image: string;
  strategy: "rolling" | "canary" | "blue_green";
  target_environment: "development" | "staging" | "production";
  status:
    | "draft"
    | "pending_approval"
    | "approved"
    | "in_progress"
    | "canary_validating"
    | "promoted"
    | "completed"
    | "failed"
    | "rollback_pending_approval"
    | "rollback_approved"
    | "rolling_back"
    | "rolled_back";
  canary_weight_percentage?: number;
  slo_passed_count?: number;
  slo_total_count?: number;
  migrations_count?: number;
  deploy_approved?: boolean;
  rollback_approved?: boolean;
}

export interface DeploymentDashboardProps {
  plans: ReleasePlanDisplay[];
  selectedPlanId?: string | undefined;
  onSelectPlan?: ((planId: string) => void) | undefined;
  onApproveDeploy?: ((planId: string) => void) | undefined;
  onRequestRollback?: ((planId: string) => void) | undefined;
  onPromoteCanary?: ((planId: string) => void) | undefined;
}

const strategyColors: Record<string, { bg: string; text: string; border: string }> = {
  canary: { bg: "bg-amber-950/60", text: "text-amber-300", border: "border-amber-700/50" },
  rolling: { bg: "bg-blue-950/60", text: "text-blue-300", border: "border-blue-700/50" },
  blue_green: {
    bg: "bg-emerald-950/60",
    text: "text-emerald-300",
    border: "border-emerald-700/50",
  },
};

const statusColors: Record<string, { bg: string; text: string; border: string }> = {
  pending_approval: {
    bg: "bg-amber-950/60",
    text: "text-amber-300",
    border: "border-amber-800/40",
  },
  approved: { bg: "bg-cyan-950/60", text: "text-cyan-300", border: "border-cyan-800/40" },
  canary_validating: {
    bg: "bg-indigo-950/60",
    text: "text-indigo-300",
    border: "border-indigo-800/40",
  },
  completed: { bg: "bg-emerald-950/60", text: "text-emerald-300", border: "border-emerald-800/40" },
  failed: { bg: "bg-rose-950/60", text: "text-rose-300", border: "border-rose-800/40" },
  rolled_back: { bg: "bg-purple-950/60", text: "text-purple-300", border: "border-purple-800/40" },
};

export const DeploymentDashboard: FC<DeploymentDashboardProps> = ({
  plans,
  selectedPlanId,
  onSelectPlan,
  onApproveDeploy,
  onRequestRollback,
  onPromoteCanary,
}) => {
  const selectedPlan = plans.find((p) => p.id === selectedPlanId) ?? plans[0];
  const activeCount = plans.filter(
    (p) => p.status === "in_progress" || p.status === "canary_validating",
  ).length;
  const completedCount = plans.filter((p) => p.status === "completed").length;
  const rolledBackCount = plans.filter((p) => p.status === "rolled_back").length;

  return (
    <div className="space-y-6" data-testid="deployment-dashboard">
      {/* Header Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Total Releases
          </p>
          <p className="mt-1 text-2xl font-black text-white">{plans.length}</p>
        </div>
        <div className="rounded-xl border border-indigo-800/40 bg-indigo-950/30 p-4 backdrop-blur">
          <p className="text-xs font-medium text-indigo-300 uppercase tracking-wider">
            Active Deployments
          </p>
          <p className="mt-1 text-2xl font-black text-indigo-400">{activeCount}</p>
        </div>
        <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/30 p-4 backdrop-blur">
          <p className="text-xs font-medium text-emerald-300 uppercase tracking-wider">
            Completed Releases
          </p>
          <p className="mt-1 text-2xl font-black text-emerald-400">{completedCount}</p>
        </div>
        <div className="rounded-xl border border-purple-800/40 bg-purple-950/30 p-4 backdrop-blur">
          <p className="text-xs font-medium text-purple-300 uppercase tracking-wider">
            Rollbacks Verified
          </p>
          <p className="mt-1 text-2xl font-black text-purple-400">{rolledBackCount}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Release Plans List */}
        <div className="space-y-3 lg:col-span-1">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Release Plans
          </h2>
          {plans.map((p) => {
            const isSelected = selectedPlan?.id === p.id;
            const strat = strategyColors[p.strategy] ?? {
              bg: "bg-slate-800",
              text: "text-slate-300",
              border: "border-slate-700",
            };
            const st = statusColors[p.status] ?? {
              bg: "bg-slate-800",
              text: "text-slate-300",
              border: "border-slate-700",
            };

            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelectPlan?.(p.id)}
                className={`w-full rounded-xl border p-4 text-left transition-all ${
                  isSelected
                    ? "border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-950/50"
                    : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/70"
                }`}
                data-testid={`plan-item-${p.id}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-white">{p.title}</h3>
                    <p className="text-xs text-slate-400">
                      v{p.version} • {p.target_environment}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${st.bg} ${st.text} ${st.border} border`}
                  >
                    {p.status.replace("_", " ")}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${strat.bg} ${strat.text} ${strat.border} border`}
                  >
                    {p.strategy}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {p.artifact_digest.slice(0, 12)}...
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Plan Details & Actions */}
        <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur lg:col-span-2">
          {selectedPlan ? (
            <>
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedPlan.title}</h2>
                  <p className="text-sm text-slate-400">
                    Version{" "}
                    <span className="font-mono text-indigo-400">{selectedPlan.version}</span> •
                    Environment:{" "}
                    <span className="uppercase text-slate-300 font-semibold">
                      {selectedPlan.target_environment}
                    </span>
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {selectedPlan.status === "pending_approval" && (
                    <button
                      type="button"
                      onClick={() => onApproveDeploy?.(selectedPlan.id)}
                      className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-emerald-500 shadow-md shadow-emerald-950"
                      data-testid="approve-deploy-btn"
                    >
                      Approve Deploy (SoD)
                    </button>
                  )}
                  {selectedPlan.status === "canary_validating" && (
                    <button
                      type="button"
                      onClick={() => onPromoteCanary?.(selectedPlan.id)}
                      className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-indigo-500 shadow-md shadow-indigo-950"
                      data-testid="promote-canary-btn"
                    >
                      Promote Canary
                    </button>
                  )}
                  {selectedPlan.status !== "rolled_back" && selectedPlan.status !== "draft" && (
                    <button
                      type="button"
                      onClick={() => onRequestRollback?.(selectedPlan.id)}
                      className="rounded-lg border border-purple-800 bg-purple-950/50 px-4 py-2 text-xs font-bold text-purple-300 transition hover:bg-purple-900/60"
                      data-testid="request-rollback-btn"
                    >
                      Rollback Rehearsal
                    </button>
                  )}
                </div>
              </div>

              {/* Artifact & Security Invariants */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Artifact Digest (SHA-256)</p>
                  <p className="mt-1 font-mono text-xs text-emerald-400 break-all">
                    {selectedPlan.artifact_digest}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-xs text-slate-400">Container Image (Digest Bound)</p>
                  <p className="mt-1 font-mono text-xs text-slate-300">
                    {selectedPlan.artifact_image}
                  </p>
                </div>
              </div>

              {/* Progressive Delivery / Canary Metrics */}
              {selectedPlan.strategy === "canary" && (
                <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase text-slate-400">
                      Canary Traffic Weight
                    </span>
                    <span className="font-mono text-sm font-bold text-amber-400">
                      {selectedPlan.canary_weight_percentage ?? 10}%
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-indigo-500"
                      style={{
                        width: `${String(selectedPlan.canary_weight_percentage ?? 10)}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* SLO Health Gates */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  SLO Promotion Gates
                </h4>
                <div className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                  <span className="text-xl">🛡️</span>
                  <div>
                    <p className="text-xs font-bold text-white">Automated SLO Health Evaluation</p>
                    <p className="text-xs text-slate-400">
                      {selectedPlan.slo_passed_count ?? 1} / {selectedPlan.slo_total_count ?? 1} SLO
                      checks passing (P99 Latency &lt; 200ms, Error Rate &lt; 0.1%)
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-center text-sm text-slate-500">
              Select a release plan to inspect details.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
