import type { PatchProposal } from "@asdo/contracts";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DiffViewer } from "../src/index";

describe("DiffViewer UI Component", () => {
  const dummyProposal: PatchProposal = {
    id: "patch-12345",
    organization_id: "018f0000-0000-7000-8000-000000000001",
    work_package_id: "pkg-ui-1",
    summary: "Add authentication session refresh",
    digest_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    files: [
      {
        path: "src/auth/session.ts",
        operation: "modify",
        hunks: [
          {
            old_start: 10,
            old_lines: 2,
            new_start: 10,
            new_lines: 3,
            lines: [
              " const token = getToken();",
              "-if (!token) return null;",
              "+if (!token) refreshSession();",
              "+return token;",
            ],
          },
        ],
      },
      {
        path: "src/auth/refresh.ts",
        operation: "add",
        hunks: [
          {
            old_start: 0,
            old_lines: 0,
            new_start: 1,
            new_lines: 1,
            lines: ["+export function refreshSession() {}"],
          },
        ],
      },
    ],
    created_at: "2026-08-20T12:00:00.000Z",
  };

  it("renders summary, work package ID, and SHA-256 digest", () => {
    render(<DiffViewer proposal={dummyProposal} />);

    expect(screen.getByText("Add authentication session refresh")).toBeInTheDocument();
    expect(screen.getByText("pkg-ui-1")).toBeInTheDocument();
    expect(screen.getByTestId("patch-digest")).toHaveTextContent("sha256:e3b0c44298fc1c14...");
  });

  it("allows switching between files and displays diff lines", () => {
    render(<DiffViewer proposal={dummyProposal} />);

    // Default to first file
    expect(screen.getByText("const token = getToken();")).toBeInTheDocument();
    expect(screen.getByText("if (!token) refreshSession();")).toBeInTheDocument();

    // Click second file tab
    const secondTab = screen.getByTestId("file-tab-1");
    fireEvent.click(secondTab);

    expect(screen.getByText("export function refreshSession() {}")).toBeInTheDocument();
  });

  it("calls onApply when Apply Patch button is clicked", async () => {
    const mockApply = vi.fn().mockResolvedValue({
      proposal_id: "patch-12345",
      applied: true,
      conflicts: [],
      committed_sha: "deadbeef",
    });

    render(<DiffViewer proposal={dummyProposal} onApply={mockApply} />);

    const applyButton = screen.getByTestId("apply-patch-button");
    fireEvent.click(applyButton);

    expect(mockApply).toHaveBeenCalledWith("patch-12345");
    expect(await screen.findByText("✓ Applied")).toBeInTheDocument();
  });

  it("displays merge conflict banner on conflict result", async () => {
    const mockApply = vi.fn().mockResolvedValue({
      proposal_id: "patch-12345",
      applied: false,
      conflicts: [
        {
          path: "src/auth/session.ts",
          reason: "Target file content changed unexpectedly.",
        },
      ],
    });

    render(<DiffViewer proposal={dummyProposal} onApply={mockApply} />);

    const applyButton = screen.getByTestId("apply-patch-button");
    fireEvent.click(applyButton);

    expect(await screen.findByTestId("merge-conflict-banner")).toBeInTheDocument();
    expect(screen.getByText("Merge Conflict Detected:")).toBeInTheDocument();
    expect(screen.getByText(/Target file content changed unexpectedly/)).toBeInTheDocument();
  });
});
