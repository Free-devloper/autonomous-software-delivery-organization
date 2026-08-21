"use client";

import { useState } from "react";

import { CoordinatorView, type SpecialistAssignmentDisplay } from "@asdo/ui";

const defaultAssignments: SpecialistAssignmentDisplay[] = [
  {
    id: "asgn-1",
    role: "analyst",
    task_name: "Decompose requirements into acceptance criteria",
    owned_files: ["docs/requirements/"],
    constraints: ["Preserve user invariants", "No assumptions without confirmation"],
    status: "completed",
    output_summary: "Structured acceptance criteria and trace links established",
  },
  {
    id: "asgn-2",
    role: "architect",
    task_name: "Generate work packages and dependency DAG",
    owned_files: ["docs/adr/", "packages/contracts/"],
    constraints: ["Provider-neutral interfaces", "Strict typed contracts"],
    status: "completed",
    output_summary: "Work packages WP-1 through WP-4 and dependency graph created",
  },
  {
    id: "asgn-3",
    role: "coder",
    task_name: "Sandboxed implementation of domain logic and contracts",
    owned_files: ["services/", "packages/"],
    constraints: ["Sandbox filesystem guard", "Default-deny network", "Zero secrets in logs"],
    status: "completed",
    output_summary: "Content-addressed patch generated and verified in worktree",
  },
  {
    id: "asgn-4",
    role: "tester",
    task_name: "Generate and execute unit, property, security, and mutation tests",
    owned_files: ["tests/"],
    constraints: [">=90% code coverage", ">=80% mutation score", "Zero flaky tests"],
    status: "completed",
    output_summary: "149 unit/integration/security tests passing with 91.3% coverage",
  },
  {
    id: "asgn-5",
    role: "reviewer",
    task_name: "Independent read-only review and separation-of-duties check",
    owned_files: [],
    constraints: [
      "Read-only inspection",
      "Verify tenant isolation",
      "Check approval digest binding",
    ],
    status: "completed",
    output_summary: "Review approved with zero high-severity findings and valid digest binding",
  },
  {
    id: "asgn-6",
    role: "release_manager",
    task_name: "Stage canary release and verify SLO health gates",
    owned_files: ["infra/"],
    constraints: ["Separate deploy/rollback approvals", "Automatic rollback on SLO breach"],
    status: "completed",
    output_summary: "Canary deployment promoted; post-rollback drill verified",
  },
];

export default function CoordinatorPage() {
  const [assignments] = useState<SpecialistAssignmentDisplay[]>(defaultAssignments);

  const handleTriggerPipeline = () => {
    // simulated dispatch
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Coordinator Agent &amp; Specialist Team
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Multi-agent delivery pipeline orchestrating Analyst, Architect, Coder, Tester, Reviewer,
            and Release Manager according to AGENTS.md.
          </p>
        </div>

        <CoordinatorView
          pipelineTitle="Autonomous End-to-End Feature Delivery Pipeline"
          requirementId="REQ-AUTONOMOUS-SDO-001"
          artifactDigest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
          status="completed"
          assignments={assignments}
          onTriggerPipeline={handleTriggerPipeline}
        />
      </div>
    </div>
  );
}
