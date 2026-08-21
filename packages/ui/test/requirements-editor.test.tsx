import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ClarificationRequest, RequirementRevision } from "@asdo/contracts";

import { RequirementsEditor } from "../src/requirements-editor";

describe("RequirementsEditor component", () => {
  const sampleRevision: RequirementRevision = {
    id: "rev-1",
    requirement_id: "req-1",
    version: 1,
    title: "OIDC Authentication",
    description: "Support Keycloak and OAuth2 provider integration.",
    scope: "services/api/auth.py",
    acceptance_criteria: [
      {
        id: "ac-1",
        criterion_text: "Validate RS256 token signatures",
        verification_method: "automated_test",
        is_mandatory: true,
      },
      {
        id: "ac-2",
        criterion_text: "Enforce actor roles",
        verification_method: "automated_test",
        is_mandatory: true,
      },
    ],
    status: "approved",
    author_id: "usr-1",
    created_at: "2026-08-20T12:00:00.000Z",
  };

  const sampleHistorical: RequirementRevision[] = [
    {
      ...sampleRevision,
      id: "rev-0",
      version: 0,
      status: "superseded",
      title: "OIDC Initial Draft",
    },
    sampleRevision,
  ];

  const sampleClarifications: ClarificationRequest[] = [
    {
      id: "clar-1",
      requirement_id: "req-1",
      question: "Which token algorithms should be allowed?",
      options: ["RS256", "ES256"],
      status: "pending",
      created_at: "2026-08-20T12:00:00.000Z",
    },
  ];

  it("renders requirement title, version, and acceptance criteria", () => {
    render(<RequirementsEditor currentRevision={sampleRevision} />);

    expect(screen.getByText("OIDC Authentication")).toBeVisible();
    expect(screen.getByTestId("version-badge")).toHaveTextContent("v1");
    expect(screen.getByTestId("status-badge")).toHaveTextContent("approved");
    expect(screen.getByText("Validate RS256 token signatures")).toBeVisible();
    expect(screen.getByText("Enforce actor roles")).toBeVisible();
  });

  it("switches revisions when clicking historical revision buttons", () => {
    render(
      <RequirementsEditor
        currentRevision={sampleRevision}
        historicalRevisions={sampleHistorical}
      />,
    );

    expect(screen.getByTestId("rev-btn-v0")).toBeVisible();
    fireEvent.click(screen.getByTestId("rev-btn-v0"));
    expect(screen.getByText("OIDC Initial Draft")).toBeVisible();
    expect(screen.getByTestId("version-badge")).toHaveTextContent("v0");
  });

  it("submits clarification answers via button selection and manual typing", () => {
    const onResolve = vi.fn();
    render(
      <RequirementsEditor
        currentRevision={sampleRevision}
        clarifications={sampleClarifications}
        onResolveClarification={onResolve}
      />,
    );

    expect(screen.getByTestId("clarifications-banner")).toBeVisible();
    expect(screen.getByText("Which token algorithms should be allowed?")).toBeVisible();

    // Type custom answer
    const input = screen.getByTestId("clarification-input-clar-1");
    fireEvent.change(input, { target: { value: "ES256 custom" } });
    fireEvent.click(screen.getByTestId("clarification-submit-clar-1"));

    expect(onResolve).toHaveBeenCalledWith("clar-1", "ES256 custom");
  });

  it("handles new revision form creation and cancel", () => {
    const onCreateRevision = vi.fn();
    render(
      <RequirementsEditor currentRevision={sampleRevision} onCreateRevision={onCreateRevision} />,
    );

    const newRevBtn = screen.getByTestId("new-revision-btn");
    fireEvent.click(newRevBtn);

    expect(screen.getByTestId("new-revision-form")).toBeVisible();
    const titleInput = screen.getByTestId("revision-title-input");
    fireEvent.change(titleInput, { target: { value: "OIDC Authentication v2" } });

    const descInput = screen.getByTestId("revision-desc-input");
    fireEvent.change(descInput, { target: { value: "Updated description text" } });

    fireEvent.click(screen.getByTestId("save-revision-btn"));
    expect(onCreateRevision).toHaveBeenCalledWith(
      "OIDC Authentication v2",
      "Updated description text",
    );
  });
});
