import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  ReviewDashboard,
  type PullRequestSummary,
  type ReviewCommentDisplay,
} from "../src/review-dashboard";

const mockPrs: PullRequestSummary[] = [
  {
    id: "pr-001",
    provider: "github",
    repository: "org/repo",
    pr_number: 42,
    title: "feat: add review system",
    state: "open",
    author_id: "u-001",
    head_sha: "abc123",
    source_branch: "feature/reviews",
    target_branch: "main",
    approvals_count: 2,
    comments_count: 5,
    has_separation_of_duties: true,
    created_at: "2026-08-01T00:00:00Z",
  },
  {
    id: "pr-002",
    provider: "gitlab",
    repository: "group/project",
    pr_number: 7,
    title: "fix: patch bug",
    state: "merged",
    author_id: "u-002",
    head_sha: "def456",
    source_branch: "fix/patch",
    target_branch: "main",
    approvals_count: 1,
    comments_count: 2,
    has_separation_of_duties: false,
    created_at: "2026-08-02T00:00:00Z",
  },
];

const mockComments: ReviewCommentDisplay[] = [
  {
    id: "c-001",
    author_id: "u-003",
    file_path: "src/main.ts",
    line_number: 10,
    body: "Please add a test",
    resolved: false,
    created_at: "2026-08-01T01:00:00Z",
  },
  {
    id: "c-002",
    author_id: "u-001",
    file_path: "src/main.ts",
    line_number: 10,
    body: "Done!",
    resolved: true,
    parent_id: "c-001",
    created_at: "2026-08-01T02:00:00Z",
  },
];

describe("ReviewDashboard", () => {
  it("renders the dashboard with pull requests", () => {
    render(<ReviewDashboard pullRequests={mockPrs} />);
    expect(screen.getByTestId("review-dashboard")).toBeInTheDocument();
    expect(screen.getByText("Code Reviews & Pull Requests")).toBeInTheDocument();
    expect(screen.getByText("1 open")).toBeInTheDocument();
  });

  it("shows PR items with provider icons", () => {
    render(<ReviewDashboard pullRequests={mockPrs} />);
    expect(screen.getByTestId("pr-item-pr-001")).toBeInTheDocument();
    expect(screen.getByTestId("pr-item-pr-002")).toBeInTheDocument();
    expect(screen.getByText("#42")).toBeInTheDocument();
  });

  it("shows separation of duties warning", () => {
    render(<ReviewDashboard pullRequests={mockPrs} />);
    expect(screen.getByTestId("duties-warning-pr-002")).toBeInTheDocument();
  });

  it("shows comments when a PR is selected", () => {
    render(
      <ReviewDashboard pullRequests={mockPrs} comments={mockComments} selectedPrId="pr-001" />,
    );
    expect(screen.getByTestId("pr-details")).toBeInTheDocument();
    expect(screen.getByText("Please add a test")).toBeInTheDocument();
    expect(screen.getByText("✓ Resolved")).toBeInTheDocument();
  });

  it("calls onSelectPr when clicking a PR", () => {
    const handler = vi.fn();
    render(<ReviewDashboard pullRequests={mockPrs} onSelectPr={handler} />);
    screen.getByTestId("pr-item-pr-001").click();
    expect(handler).toHaveBeenCalledWith("pr-001");
  });

  it("shows empty state when no PRs", () => {
    render(<ReviewDashboard pullRequests={[]} />);
    expect(screen.getByTestId("empty-pr-list")).toBeInTheDocument();
  });
});
