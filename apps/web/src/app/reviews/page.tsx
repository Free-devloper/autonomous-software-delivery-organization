"use client";

import { useState } from "react";

import { ReviewDashboard, type PullRequestSummary, type ReviewCommentDisplay } from "@asdo/ui";

const demoPrs: PullRequestSummary[] = [
  {
    id: "pr-001",
    provider: "github",
    repository: "asdo/platform",
    pr_number: 142,
    title: "feat: implement review system with digest-bound approvals",
    state: "open",
    author_id: "architect-agent",
    head_sha: "a1b2c3d4e5f6",
    source_branch: "feature/review-system",
    target_branch: "main",
    approvals_count: 1,
    comments_count: 3,
    has_separation_of_duties: true,
    created_at: "2026-08-18T10:00:00Z",
  },
  {
    id: "pr-002",
    provider: "github",
    repository: "asdo/platform",
    pr_number: 141,
    title: "feat: security scanning and quality gates",
    state: "merged",
    author_id: "security-agent",
    head_sha: "b2c3d4e5f6a1",
    source_branch: "feature/security-gates",
    target_branch: "main",
    approvals_count: 2,
    comments_count: 7,
    has_separation_of_duties: true,
    created_at: "2026-08-17T14:00:00Z",
  },
  {
    id: "pr-003",
    provider: "gitlab",
    repository: "asdo/infrastructure",
    pr_number: 38,
    title: "fix: sandbox network policy deny-by-default",
    state: "open",
    author_id: "coding-agent",
    head_sha: "c3d4e5f6a1b2",
    source_branch: "fix/sandbox-network",
    target_branch: "main",
    approvals_count: 0,
    comments_count: 1,
    has_separation_of_duties: false,
    created_at: "2026-08-19T09:30:00Z",
  },
  {
    id: "pr-004",
    provider: "github",
    repository: "asdo/platform",
    pr_number: 140,
    title: "chore: update dependencies and lock file",
    state: "closed",
    author_id: "dependency-bot",
    head_sha: "d4e5f6a1b2c3",
    source_branch: "chore/deps",
    target_branch: "main",
    approvals_count: 0,
    comments_count: 0,
    has_separation_of_duties: true,
    created_at: "2026-08-16T08:00:00Z",
  },
];

const demoComments: Record<string, ReviewCommentDisplay[]> = {
  "pr-001": [
    {
      id: "c-001",
      author_id: "reviewer-agent",
      file_path: "services/api/src/reviews/service.py",
      line_number: 45,
      body: "Consider adding rate limiting to the approval endpoint to prevent abuse.",
      resolved: false,
      created_at: "2026-08-18T11:00:00Z",
    },
    {
      id: "c-002",
      author_id: "architect-agent",
      file_path: "services/api/src/reviews/service.py",
      line_number: 45,
      body: "Good point — I'll add a configurable rate limiter in the next commit.",
      resolved: false,
      parent_id: "c-001",
      created_at: "2026-08-18T11:30:00Z",
    },
    {
      id: "c-003",
      author_id: "reviewer-agent",
      file_path: "packages/contracts/src/v1/reviews.ts",
      line_number: 12,
      body: "The approval schema should enforce SHA-256 digest format (64 hex chars). ✓ Already done!",
      resolved: true,
      created_at: "2026-08-18T12:00:00Z",
    },
  ],
  "pr-003": [
    {
      id: "c-004",
      author_id: "security-agent",
      file_path: "services/api/src/sandbox/network_guard.py",
      line_number: 8,
      body: "The default-deny policy needs explicit egress rules for DNS resolution.",
      resolved: false,
      created_at: "2026-08-19T10:00:00Z",
    },
  ],
};

export default function ReviewsPage() {
  const [selectedPrId, setSelectedPrId] = useState<string | undefined>(undefined);
  const emptyComments: ReviewCommentDisplay[] = [];
  const activeComments = demoComments[selectedPrId ?? ""] ?? emptyComments;

  const openCount = demoPrs.filter((pr: PullRequestSummary) => pr.state === "open").length;
  const mergedCount = demoPrs.filter((pr: PullRequestSummary) => pr.state === "merged").length;
  const pendingCount = demoPrs.filter(
    (pr: PullRequestSummary) => pr.state === "open" && pr.approvals_count === 0,
  ).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 md:p-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            Code Reviews & Pull Requests
          </h1>
          <p className="text-sm text-slate-400">
            Digest-bound approvals, threaded comments, separation of duties enforcement, and
            idempotent PR operations across GitHub and GitLab.
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            {
              label: "Total PRs",
              value: demoPrs.length,
              color: "text-indigo-400",
            },
            {
              label: "Open",
              value: openCount,
              color: "text-emerald-400",
            },
            {
              label: "Merged",
              value: mergedCount,
              color: "text-violet-400",
            },
            {
              label: "Pending Review",
              value: pendingCount,
              color: "text-amber-400",
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col gap-1 rounded-xl border border-slate-800 bg-slate-900/60 p-4"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {stat.label}
              </span>
              <span className={`text-2xl font-black ${stat.color}`}>{String(stat.value)}</span>
            </div>
          ))}
        </div>

        <ReviewDashboard
          pullRequests={demoPrs}
          comments={activeComments}
          selectedPrId={selectedPrId}
          onSelectPr={setSelectedPrId}
        />
      </div>
    </div>
  );
}
