import React from "react";

/** Pull request summary for display. */
export interface PullRequestSummary {
  id: string;
  provider: "github" | "gitlab";
  repository: string;
  pr_number: number;
  title: string;
  state: "open" | "closed" | "merged" | "draft";
  author_id: string;
  head_sha: string;
  source_branch: string;
  target_branch: string;
  approvals_count: number;
  comments_count: number;
  has_separation_of_duties: boolean;
  created_at: string;
}

/** Review comment for display. */
export interface ReviewCommentDisplay {
  id: string;
  author_id: string;
  file_path: string;
  line_number: number;
  body: string;
  resolved: boolean;
  parent_id?: string;
  created_at: string;
}

export interface ReviewDashboardProps {
  pullRequests: PullRequestSummary[];
  comments?: ReviewCommentDisplay[];
  onSelectPr?: (prId: string) => void;
  selectedPrId?: string | undefined;
}

const stateColors: Record<string, { bg: string; text: string; border: string }> = {
  open: {
    bg: "bg-emerald-950/60",
    text: "text-emerald-300",
    border: "border-emerald-800/40",
  },
  merged: {
    bg: "bg-violet-950/60",
    text: "text-violet-300",
    border: "border-violet-800/40",
  },
  closed: {
    bg: "bg-slate-800/60",
    text: "text-slate-400",
    border: "border-slate-700/40",
  },
  draft: {
    bg: "bg-amber-950/60",
    text: "text-amber-300",
    border: "border-amber-800/40",
  },
};

const providerIcons: Record<string, string> = {
  github: "🐙",
  gitlab: "🦊",
};

/**
 * ReviewDashboard — shows pull requests, approvals, threaded comments, and
 * separation-of-duties status.
 */
export function ReviewDashboard({
  pullRequests,
  comments = [],
  onSelectPr,
  selectedPrId,
}: ReviewDashboardProps): React.JSX.Element {
  const openCount = pullRequests.filter((pr) => pr.state === "open").length;
  const mergedCount = pullRequests.filter((pr) => pr.state === "merged").length;
  const selectedPr = pullRequests.find((pr) => pr.id === selectedPrId);

  return (
    <div
      className="flex flex-col gap-6 rounded-xl border border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-xl"
      data-testid="review-dashboard"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 text-lg font-bold">
            📝
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">
              Code Reviews & Pull Requests
            </h2>
            <p className="text-xs text-slate-400">
              {pullRequests.length} pull request{pullRequests.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <span className="rounded-md bg-emerald-950/60 px-2 py-1 text-xs font-bold text-emerald-300">
            {openCount} open
          </span>
          <span className="rounded-md bg-violet-950/60 px-2 py-1 text-xs font-bold text-violet-300">
            {mergedCount} merged
          </span>
        </div>
      </div>

      {/* PR List */}
      <div className="flex flex-col gap-2" data-testid="pr-list">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Pull Requests</h3>
        {pullRequests.length === 0 ? (
          <p className="text-sm text-slate-500" data-testid="empty-pr-list">
            No pull requests found.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-2">
            {pullRequests.map((pr) => {
              const defaultColor = {
                bg: "bg-slate-800/60",
                text: "text-slate-400",
                border: "border-slate-700/40",
              };
              const colors = stateColors[pr.state] ?? defaultColor;
              const isSelected = pr.id === selectedPrId;
              return (
                <button
                  key={pr.id}
                  type="button"
                  onClick={() => onSelectPr?.(pr.id)}
                  className={`flex items-center justify-between rounded-lg border p-3 text-left transition-all ${
                    isSelected
                      ? "border-indigo-500 bg-indigo-950/40"
                      : `${colors.border} ${colors.bg} hover:border-slate-600`
                  }`}
                  data-testid={`pr-item-${pr.id}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{providerIcons[pr.provider]}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">{pr.title}</span>
                        <span className="text-xs text-slate-500">#{pr.pr_number}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>{pr.repository}</span>
                        <span>•</span>
                        <span>
                          {pr.source_branch} → {pr.target_branch}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {!pr.has_separation_of_duties && (
                      <span
                        className="text-xs font-bold text-rose-400"
                        data-testid={`duties-warning-${pr.id}`}
                      >
                        ⚠ duties
                      </span>
                    )}
                    <span className="text-xs text-slate-400">💬 {pr.comments_count}</span>
                    <span className="text-xs text-slate-400">✅ {pr.approvals_count}</span>
                    <span
                      className={`rounded-md px-2 py-1 text-[10px] font-bold uppercase ${colors.bg} ${colors.text} border ${colors.border}`}
                    >
                      {pr.state}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Selected PR Details: Comments */}
      {selectedPr && (
        <div className="flex flex-col gap-3" data-testid="pr-details">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Comments on #{selectedPr.pr_number}
          </h3>
          {comments.length === 0 ? (
            <p className="text-sm text-slate-500">No comments yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {comments.map((comment) => (
                <div
                  key={comment.id}
                  className={`rounded-lg border p-3 ${
                    comment.resolved
                      ? "border-slate-800 bg-slate-900/40 opacity-60"
                      : "border-slate-700 bg-slate-900/60"
                  } ${comment.parent_id ? "ml-6" : ""}`}
                  data-testid={`comment-${comment.id}`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-300">{comment.author_id}</span>
                      <span className="text-slate-500">
                        {comment.file_path}:{comment.line_number}
                      </span>
                    </div>
                    {comment.resolved && <span className="text-emerald-400">✓ Resolved</span>}
                  </div>
                  <p className="mt-1 text-sm text-slate-300">{comment.body}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
