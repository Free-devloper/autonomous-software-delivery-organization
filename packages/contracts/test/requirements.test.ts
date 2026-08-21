import { describe, expect, it } from "vitest";

import {
  acceptanceCriterionSchema,
  clarificationRequestSchema,
  createRequirementRequestSchema,
  requirementRevisionSchema,
  requirementStatusSchema,
  resolveClarificationRequestSchema,
  verificationMethodSchema,
} from "../src/index";

describe("Requirements contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  it("validates acceptance criterion schema", () => {
    const criterion = {
      id: "ac_1",
      criterion_text: "All API endpoints must return 401 for unauthenticated requests.",
      verification_method: "automated_test" as const,
      is_mandatory: true,
    };
    expect(acceptanceCriterionSchema.parse(criterion)).toEqual(criterion);
  });

  it("validates requirement revision schema", () => {
    const revision = {
      id: "rev_018f",
      requirement_id: "req_018f",
      version: 1,
      title: "OAuth2 Provider Integration",
      description: "Implement Keycloak-compatible OIDC token validation.",
      scope: "services/api/src/autonomous_sdo_api/auth.py",
      acceptance_criteria: [
        {
          id: "ac_1",
          criterion_text: "Reject expired JWT tokens.",
          verification_method: "automated_test" as const,
          is_mandatory: true,
        },
      ],
      status: "approved" as const,
      author_id: "usr_lead_1",
      created_at: timestamp,
    };
    expect(requirementRevisionSchema.parse(revision)).toEqual(revision);
  });

  it("validates clarification request and resolve schemas", () => {
    const clarification = {
      id: "clar_1",
      requirement_id: "req_018f",
      question: "Which token encryption algorithms should be accepted?",
      options: ["RS256 only", "RS256 and ES256"],
      status: "pending" as const,
      created_at: timestamp,
    };
    expect(clarificationRequestSchema.parse(clarification)).toEqual(clarification);

    const resolvePayload = { response: "RS256 only" };
    expect(resolveClarificationRequestSchema.parse(resolvePayload)).toEqual(resolvePayload);
  });

  it("validates create requirement request schema", () => {
    const payload = {
      title: "Task Queue Integration",
      description: "Integrate Temporal workflow orchestrator.",
      scope: "services/workflow",
      acceptance_criteria: [
        {
          id: "ac_1",
          criterion_text: "Workflows must survive worker restart.",
          verification_method: "automated_test" as const,
          is_mandatory: true,
        },
      ],
    };
    expect(createRequirementRequestSchema.parse(payload)).toEqual(payload);
  });

  it("rejects invalid verification methods and statuses", () => {
    expect(() => verificationMethodSchema.parse("invalid_method")).toThrow();
    expect(() => requirementStatusSchema.parse("invalid_status")).toThrow();
  });
});
