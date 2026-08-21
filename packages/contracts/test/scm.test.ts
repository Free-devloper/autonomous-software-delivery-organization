import { describe, expect, it } from "vitest";

import {
  commitResolutionSchema,
  normalizedWebhookEventSchema,
  repositoryDescriptorSchema,
} from "../src/index";

describe("SCM contracts", () => {
  it("validates a standard repository descriptor", () => {
    const validRepo = {
      provider: "github" as const,
      id: "repo-123",
      owner: "roytechworkforce",
      name: "autonomous-software-delivery-organization",
      full_name: "roytechworkforce/autonomous-software-delivery-organization",
      default_branch: "main",
      visibility: "private" as const,
      clone_url_http: "https://github.com/roytechworkforce/asdo.git",
      clone_url_ssh: "git@github.com:roytechworkforce/asdo.git",
      is_archived: false,
    };

    expect(repositoryDescriptorSchema.parse(validRepo)).toEqual(validRepo);
  });

  it("validates a commit resolution with parent SHAs", () => {
    const validCommit = {
      provider: "gitlab" as const,
      repository_id: "gl-456",
      commit_sha: "e4d909c290d0fb1ca068ffaddf22cbd0adddefec",
      ref_requested: "main",
      message: "feat: initial commit",
      author_name: "Alice Engineer",
      author_email: "alice@example.com",
      authored_at: "2026-08-19T12:00:00.000Z",
      parent_shas: ["0000000000000000000000000000000000000000"],
    };

    expect(commitResolutionSchema.parse(validCommit)).toEqual(validCommit);
  });

  it("rejects invalid commit SHA format", () => {
    expect(() =>
      commitResolutionSchema.parse({
        provider: "github",
        repository_id: "repo-123",
        commit_sha: "not-a-valid-sha",
        message: "bad",
        author_name: "Bob",
        author_email: "bob@example.com",
        authored_at: "2026-08-19T12:00:00.000Z",
        parent_shas: [],
      }),
    ).toThrow();
  });

  it("validates a normalized webhook event", () => {
    const validEvent = {
      provider: "github" as const,
      event_id: "evt-789",
      event_type: "push" as const,
      repository_full_name: "roytechworkforce/asdo",
      ref: "refs/heads/main",
      before_sha: "0000000000000000000000000000000000000000",
      after_sha: "e4d909c290d0fb1ca068ffaddf22cbd0adddefec",
      sender: "octocat",
      timestamp: "2026-08-19T12:00:00.000Z",
    };

    expect(normalizedWebhookEventSchema.parse(validEvent)).toEqual(validEvent);
  });
});
