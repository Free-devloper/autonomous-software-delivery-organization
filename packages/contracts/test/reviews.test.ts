import { describe, expect, it } from "vitest";

import {
  addCommentRequestSchema,
  createPullRequestSchema,
  pullRequestSchema,
  pullRequestStateSchema,
  reviewApprovalSchema,
  reviewCommentSchema,
  reviewStatusSchema,
  submitApprovalRequestSchema,
} from "../src/v1/reviews";

describe("reviewStatusSchema", () => {
  it("accepts valid statuses", () => {
    const statuses = [
      "pending",
      "in_progress",
      "approved",
      "changes_requested",
      "dismissed",
      "expired",
    ];
    for (const s of statuses) {
      expect(reviewStatusSchema.parse(s)).toBe(s);
    }
  });

  it("rejects invalid status", () => {
    expect(() => reviewStatusSchema.parse("invalid")).toThrow();
  });
});

describe("reviewCommentSchema", () => {
  it("validates a threaded comment", () => {
    const comment = reviewCommentSchema.parse({
      id: "c-001",
      review_id: "r-001",
      author_id: "u-001",
      file_path: "src/main.ts",
      line_number: 42,
      body: "This needs refactoring",
      resolved: false,
      created_at: "2026-08-01T00:00:00Z",
    });
    expect(comment.id).toBe("c-001");
    expect(comment.resolved).toBe(false);
  });

  it("supports parent_id for threading", () => {
    const reply = reviewCommentSchema.parse({
      id: "c-002",
      review_id: "r-001",
      author_id: "u-002",
      file_path: "src/main.ts",
      line_number: 42,
      body: "Agreed, will fix",
      parent_id: "c-001",
      resolved: false,
      created_at: "2026-08-01T01:00:00Z",
    });
    expect(reply.parent_id).toBe("c-001");
  });
});

describe("reviewApprovalSchema", () => {
  it("validates a digest-bound approval", () => {
    const digest = "a".repeat(64);
    const approval = reviewApprovalSchema.parse({
      id: "a-001",
      review_id: "r-001",
      approver_id: "u-003",
      artifact_digest: digest,
      scope: "deploy",
      environment: "production",
      status: "approved",
      expires_at: "2026-09-01T00:00:00Z",
      created_at: "2026-08-01T00:00:00Z",
      is_stale: false,
    });
    expect(approval.artifact_digest).toBe(digest);
    expect(approval.status).toBe("approved");
  });

  it("rejects short digest", () => {
    expect(() =>
      reviewApprovalSchema.parse({
        id: "a-002",
        review_id: "r-001",
        approver_id: "u-003",
        artifact_digest: "short",
        scope: "deploy",
        environment: "production",
        status: "approved",
        expires_at: "2026-09-01T00:00:00Z",
        created_at: "2026-08-01T00:00:00Z",
      }),
    ).toThrow();
  });
});

describe("pullRequestSchema", () => {
  it("validates a pull request with approvals and comments", () => {
    const pr = pullRequestSchema.parse({
      id: "pr-001",
      organization_id: "550e8400-e29b-41d4-a716-446655440000",
      provider: "github",
      repository: "org/repo",
      pr_number: 42,
      title: "feat: add review system",
      source_branch: "feature/reviews",
      target_branch: "main",
      state: "open",
      author_id: "u-001",
      head_sha: "abc123",
      created_at: "2026-08-01T00:00:00Z",
    });
    expect(pr.pr_number).toBe(42);
    expect(pr.approvals).toEqual([]);
    expect(pr.comments).toEqual([]);
  });
});

describe("pullRequestStateSchema", () => {
  it("accepts all valid states", () => {
    const states = ["open", "closed", "merged", "draft"];
    for (const s of states) {
      expect(pullRequestStateSchema.parse(s)).toBe(s);
    }
  });
});

describe("createPullRequestSchema", () => {
  it("validates a PR creation request", () => {
    const req = createPullRequestSchema.parse({
      provider: "gitlab",
      repository: "group/project",
      title: "feat: new feature",
      source_branch: "feature/x",
      target_branch: "main",
      head_sha: "def456",
    });
    expect(req.provider).toBe("gitlab");
    expect(req.description).toBe("");
  });
});

describe("submitApprovalRequestSchema", () => {
  it("validates an approval submission", () => {
    const digest = "b".repeat(64);
    const req = submitApprovalRequestSchema.parse({
      artifact_digest: digest,
      scope: "deploy",
      environment: "staging",
    });
    expect(req.expires_in_hours).toBe(24);
  });
});

describe("addCommentRequestSchema", () => {
  it("validates a comment request", () => {
    const req = addCommentRequestSchema.parse({
      file_path: "src/app.ts",
      line_number: 10,
      body: "Please add a test",
    });
    expect(req.parent_id).toBeUndefined();
  });
});
