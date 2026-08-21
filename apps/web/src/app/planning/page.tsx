"use client";

import { useState } from "react";
import type { ArchitecturePlan } from "@asdo/contracts";
import { PlanViewer } from "@asdo/ui";

const defaultPlan: ArchitecturePlan = {
  id: "plan_auth_018f",
  requirement_id: "req_auth_01",
  revision_id: "rev_018f0001",
  summary:
    "Decomposition of multi-tenant OIDC authentication and path containment security into backend and test work packages.",
  work_packages: [
    {
      id: "wp_backend_auth",
      requirement_id: "req_auth_01",
      revision_id: "rev_018f0001",
      title: "Backend Token Verifier & Path Containment",
      description: "Implement OIDC token verifier and path containment security guard.",
      target_files: [
        "services/api/src/autonomous_sdo_api/auth.py",
        "services/api/src/autonomous_sdo_api/repository/path_guard.py",
      ],
      acceptance_criteria_ids: ["ac_1", "ac_3"],
      dependencies: [],
      assigned_specialist: "backend",
      budget: {
        max_tokens: 30000,
        max_duration_seconds: 240,
        max_cost_usd: 1.5,
      },
      status: "completed",
      created_at: "2026-08-20T00:00:00.000Z",
    },
    {
      id: "wp_testing_security",
      requirement_id: "req_auth_01",
      revision_id: "rev_018f0001",
      title: "Security & Penetration Test Suite",
      description:
        "Cross-tenant RLS isolation tests, path traversal fuzzing, and expired token rejection.",
      target_files: ["services/api/tests/test_auth.py", "services/api/tests/test_repository.py"],
      acceptance_criteria_ids: ["ac_1", "ac_2", "ac_3"],
      dependencies: ["wp_backend_auth"],
      assigned_specialist: "testing",
      budget: {
        max_tokens: 20000,
        max_duration_seconds: 180,
        max_cost_usd: 1.0,
      },
      status: "pending",
      created_at: "2026-08-20T00:05:00.000Z",
    },
  ],
  edges: [{ from_package_id: "wp_backend_auth", to_package_id: "wp_testing_security" }],
  total_budget: {
    max_tokens: 50000,
    max_duration_seconds: 420,
    max_cost_usd: 2.5,
  },
  is_approved: false,
  created_at: "2026-08-20T00:00:00.000Z",
};

export default function PlanningPage() {
  const [plan, setPlan] = useState<ArchitecturePlan>(defaultPlan);

  const handleApprovePlan = (planId: string, rationale: string) => {
    setPlan((prev) => ({
      ...prev,
      is_approved: true,
      approval_rationale: rationale,
      approved_by: "usr_lead_architect",
    }));
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Architecture & Work Packages
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Verified dependency DAGs, specialist agent assignments, and bounded execution budgets.
            </p>
          </div>
        </header>

        <PlanViewer plan={plan} onApprovePlan={handleApprovePlan} />
      </div>
    </main>
  );
}
