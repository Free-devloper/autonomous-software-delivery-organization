"use client";

import { useState } from "react";

import { DeploymentDashboard, type ReleasePlanDisplay } from "@asdo/ui";

const demoPlans: ReleasePlanDisplay[] = [
  {
    id: "rel-001",
    title: "v1.0.0 Production Release",
    version: "1.0.0",
    artifact_digest: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    artifact_image: "ghcr.io/roytechworkforce/asdo:1.0.0",
    strategy: "canary",
    target_environment: "production",
    status: "canary_validating",
    canary_weight_percentage: 20,
    slo_passed_count: 3,
    slo_total_count: 3,
    migrations_count: 1,
    deploy_approved: true,
  },
  {
    id: "rel-002",
    title: "v0.9.0 Staging Release",
    version: "0.9.0",
    artifact_digest: "ca978112ca1bbdcafac231b39a23dc4da786081441609261c65779532163973c",
    artifact_image: "ghcr.io/roytechworkforce/asdo:0.9.0",
    strategy: "rolling",
    target_environment: "staging",
    status: "completed",
    slo_passed_count: 2,
    slo_total_count: 2,
    migrations_count: 0,
    deploy_approved: true,
  },
  {
    id: "rel-003",
    title: "v1.1.0 RC Candidate",
    version: "1.1.0-rc1",
    artifact_digest: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    artifact_image: "ghcr.io/roytechworkforce/asdo:1.1.0-rc1",
    strategy: "canary",
    target_environment: "staging",
    status: "pending_approval",
    canary_weight_percentage: 10,
    slo_passed_count: 1,
    slo_total_count: 1,
    migrations_count: 0,
    deploy_approved: false,
  },
];

export default function DeploymentPage() {
  const [plans, setPlans] = useState<ReleasePlanDisplay[]>(demoPlans);
  const [selectedPlanId, setSelectedPlanId] = useState<string | undefined>("rel-001");

  const handleApproveDeploy = (planId: string) => {
    setPlans((prev) =>
      prev.map((p) =>
        p.id === planId ? { ...p, status: "approved" as const, deploy_approved: true } : p,
      ),
    );
  };

  const handlePromoteCanary = (planId: string) => {
    setPlans((prev) =>
      prev.map((p) => (p.id === planId ? { ...p, status: "completed" as const } : p)),
    );
  };

  const handleRequestRollback = (planId: string) => {
    setPlans((prev) =>
      prev.map((p) =>
        p.id === planId ? { ...p, status: "rolled_back" as const, rollback_approved: true } : p,
      ),
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Progressive Delivery &amp; Rollback
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Immutable artifact releases, canary traffic splitting, automated SLO health gates, and
            purpose-separated rollback rehearsals.
          </p>
        </div>

        <DeploymentDashboard
          plans={plans}
          selectedPlanId={selectedPlanId}
          onSelectPlan={setSelectedPlanId}
          onApproveDeploy={handleApproveDeploy}
          onPromoteCanary={handlePromoteCanary}
          onRequestRollback={handleRequestRollback}
        />
      </div>
    </div>
  );
}
