"use client";

import { useState } from "react";
import type { ClarificationRequest, RequirementRevision } from "@asdo/contracts";
import { RequirementsEditor } from "@asdo/ui";

const defaultRequirement: RequirementRevision = {
  id: "rev_018f0001",
  requirement_id: "req_auth_01",
  version: 1,
  title: "Multi-Tenant OIDC & Worktree Security",
  description:
    "Production-grade tenant isolation using PostgreSQL Row-Level Security, Keycloak-compatible OIDC token validation, and path traversal guards.",
  scope:
    "services/api/src/autonomous_sdo_api/auth.py, services/api/src/autonomous_sdo_api/database/tenancy.py",
  acceptance_criteria: [
    {
      id: "ac_1",
      criterion_text: "Reject expired or untrusted JWT signatures with 401 Unauthorized.",
      verification_method: "automated_test",
      is_mandatory: true,
    },
    {
      id: "ac_2",
      criterion_text: "Enforce PostgreSQL RLS tenant containment across all multi-tenant queries.",
      verification_method: "automated_test",
      is_mandatory: true,
    },
    {
      id: "ac_3",
      criterion_text:
        "Verify worktree path containment and reject null bytes and directory escapes.",
      verification_method: "security_scan",
      is_mandatory: true,
    },
  ],
  status: "approved",
  author_id: "usr_platform_lead",
  created_at: "2026-08-20T00:00:00.000Z",
};

const defaultClarifications: ClarificationRequest[] = [
  {
    id: "clar_auth_1",
    requirement_id: "req_auth_01",
    question: "Which cryptographic signature algorithms are permitted for OIDC tokens?",
    options: ["RS256 only", "RS256 and ES256"],
    response: undefined,
    status: "pending",
    created_at: "2026-08-20T00:30:00.000Z",
  },
  {
    id: "clar_auth_2",
    requirement_id: "req_auth_01",
    question: "What is the token expiration tolerance window?",
    options: ["0 seconds", "30 seconds"],
    response: undefined,
    status: "pending",
    created_at: "2026-08-20T00:35:00.000Z",
  },
];

export default function RequirementsPage() {
  const [currentRevision, setCurrentRevision] = useState<RequirementRevision>(defaultRequirement);
  const [revisions, setRevisions] = useState<RequirementRevision[]>([defaultRequirement]);
  const [clarifications, setClarifications] =
    useState<ClarificationRequest[]>(defaultClarifications);

  const handleResolveClarification = (clarId: string, response: string) => {
    setClarifications((prev) =>
      prev.map((c) =>
        c.id === clarId
          ? {
              ...c,
              response,
              status: "resolved",
              resolved_at: new Date().toISOString(),
            }
          : c,
      ),
    );
  };

  const handleCreateRevision = (title: string, description: string) => {
    const newVersion = currentRevision.version + 1;
    const newRev: RequirementRevision = {
      ...currentRevision,
      id: `rev_018f000${newVersion.toString()}`,
      version: newVersion,
      title,
      description,
      status: "draft",
      created_at: new Date().toISOString(),
    };

    setRevisions((prev) => [...prev, newRev]);
    setCurrentRevision(newRev);
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Requirements Lifecycle</h1>
            <p className="mt-1 text-sm text-slate-400">
              Immutable revision tracking, acceptance criteria, and interactive clarification
              workflows.
            </p>
          </div>
        </header>

        <RequirementsEditor
          currentRevision={currentRevision}
          historicalRevisions={revisions}
          clarifications={clarifications}
          onResolveClarification={handleResolveClarification}
          onCreateRevision={handleCreateRevision}
        />
      </div>
    </main>
  );
}
