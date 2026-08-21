import { describe, expect, it } from "vitest";

import {
  approvePlanRequestSchema,
  architecturePlanSchema,
  createPlanRequestSchema,
  specialistRoleSchema,
  workPackageBudgetSchema,
  workPackageSchema,
  workPackageStatusSchema,
} from "../src/index";

describe("Planning contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  it("validates work package budget schema", () => {
    const budget = {
      max_tokens: 50000,
      max_duration_seconds: 300,
      max_cost_usd: 2.5,
    };
    expect(workPackageBudgetSchema.parse(budget)).toEqual(budget);
  });

  it("validates work package schema", () => {
    const pkg = {
      id: "wp_backend_1",
      requirement_id: "req_01",
      revision_id: "rev_01",
      title: "Implement API Token Validation",
      description: "Add RS256 token verifier in auth service",
      target_files: ["services/api/src/auth.py"],
      acceptance_criteria_ids: ["ac_1"],
      dependencies: [],
      assigned_specialist: "backend" as const,
      budget: {
        max_tokens: 25000,
        max_duration_seconds: 180,
        max_cost_usd: 1.0,
      },
      status: "pending" as const,
      created_at: timestamp,
    };
    expect(workPackageSchema.parse(pkg)).toEqual(pkg);
  });

  it("validates architecture plan schema", () => {
    const plan = {
      id: "plan_01",
      requirement_id: "req_01",
      revision_id: "rev_01",
      summary: "Decomposition of token auth into backend and test tasks",
      work_packages: [
        {
          id: "wp_1",
          requirement_id: "req_01",
          revision_id: "rev_01",
          title: "Backend Auth",
          description: "Auth handler",
          target_files: ["services/api/src/auth.py"],
          acceptance_criteria_ids: ["ac_1"],
          dependencies: [],
          assigned_specialist: "backend" as const,
          budget: {
            max_tokens: 25000,
            max_duration_seconds: 180,
            max_cost_usd: 1.0,
          },
          status: "pending" as const,
          created_at: timestamp,
        },
      ],
      edges: [],
      total_budget: {
        max_tokens: 25000,
        max_duration_seconds: 180,
        max_cost_usd: 1.0,
      },
      is_approved: false,
      created_at: timestamp,
    };
    expect(architecturePlanSchema.parse(plan)).toEqual(plan);
  });

  it("validates create and approve plan request schemas", () => {
    const pkg = {
      id: "wp_1",
      requirement_id: "req_01",
      revision_id: "rev_01",
      title: "Backend Auth",
      description: "Auth handler",
      target_files: ["services/api/src/auth.py"],
      acceptance_criteria_ids: ["ac_1"],
      dependencies: [],
      assigned_specialist: "backend" as const,
      budget: {
        max_tokens: 25000,
        max_duration_seconds: 180,
        max_cost_usd: 1.0,
      },
      status: "pending" as const,
      created_at: timestamp,
    };
    const create = {
      requirement_id: "req_01",
      revision_id: "rev_01",
      summary: "Plan summary",
      work_packages: [pkg],
      edges: [],
    };
    expect(createPlanRequestSchema.parse(create)).toEqual(create);
    const approve = { rationale: "Verified against SRS §4 requirements" };
    expect(approvePlanRequestSchema.parse(approve)).toEqual(approve);
  });

  it("rejects invalid specialist roles and statuses", () => {
    expect(() => specialistRoleSchema.parse("invalid_role")).toThrow();
    expect(() => workPackageStatusSchema.parse("invalid_status")).toThrow();
  });
});
