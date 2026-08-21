import { describe, expect, it } from "vitest";

import {
  coverageEntrySchema,
  mutationReportSchema,
  qualityGateEvaluationSchema,
  securityFindingSchema,
  securityScanReportSchema,
  testCaseResultSchema,
  testSuiteReportSchema,
} from "../src/v1/security";

describe("security contracts", () => {
  it("validates a security finding", () => {
    const finding = {
      id: "finding-001",
      rule_id: "B101",
      tool: "bandit",
      category: "sast",
      severity: "high",
      message: "Use of assert detected.",
      file_path: "src/auth.py",
      start_line: 42,
      cwe_ids: ["CWE-703"],
    };
    expect(securityFindingSchema.parse(finding)).toMatchObject({
      id: "finding-001",
      severity: "high",
      suppressed: false,
    });
  });

  it("validates a security scan report", () => {
    const report = {
      id: "scan-001",
      organization_id: "018f0000-0000-7000-8000-000000000001",
      scan_target: "services/api",
      tool_name: "bandit",
      tool_version: "1.7.5",
      category: "sast",
      findings: [],
      total_findings: 0,
      critical_count: 0,
      high_count: 0,
      passed: true,
      scanned_at: "2026-08-20T10:00:00Z",
    };
    const parsed = securityScanReportSchema.parse(report);
    expect(parsed.passed).toBe(true);
    expect(parsed.findings).toHaveLength(0);
  });

  it("validates a test case result", () => {
    const test_case = {
      id: "tc-001",
      name: "test_login_success",
      suite: "auth",
      file_path: "tests/test_auth.py",
      status: "passed",
      duration_ms: 42.5,
    };
    const parsed = testCaseResultSchema.parse(test_case);
    expect(parsed.status).toBe("passed");
    expect(parsed.is_flaky).toBe(false);
  });

  it("validates a test suite report", () => {
    const report = {
      id: "suite-001",
      organization_id: "018f0000-0000-7000-8000-000000000001",
      suite_name: "unit",
      total_tests: 100,
      passed: 95,
      failed: 3,
      skipped: 2,
      flaky: 1,
      duration_ms: 12500,
      overall_passed: false,
      run_at: "2026-08-20T10:00:00Z",
    };
    const parsed = testSuiteReportSchema.parse(report);
    expect(parsed.overall_passed).toBe(false);
    expect(parsed.total_tests).toBe(100);
  });

  it("validates a coverage entry", () => {
    const entry = {
      file_path: "src/auth.py",
      statement_coverage: 95.5,
      branch_coverage: 88.0,
      function_coverage: 100,
      line_coverage: 94.2,
      uncovered_lines: [42, 55],
    };
    const parsed = coverageEntrySchema.parse(entry);
    expect(parsed.uncovered_lines).toEqual([42, 55]);
  });

  it("validates a mutation report", () => {
    const report = {
      id: "mut-001",
      organization_id: "018f0000-0000-7000-8000-000000000001",
      total_mutants: 200,
      killed: 180,
      survived: 15,
      timeout: 3,
      no_coverage: 2,
      mutation_score: 90.0,
      threshold: 80.0,
      passed: true,
      generated_at: "2026-08-20T10:00:00Z",
    };
    const parsed = mutationReportSchema.parse(report);
    expect(parsed.passed).toBe(true);
    expect(parsed.mutation_score).toBe(90.0);
  });

  it("validates a quality gate evaluation", () => {
    const evaluation = {
      id: "qg-001",
      organization_id: "018f0000-0000-7000-8000-000000000001",
      work_package_id: "wp-001",
      overall_status: "passed",
      checks: [
        {
          name: "coverage",
          status: "passed",
          threshold: "90%",
          actual: "92%",
        },
        {
          name: "mutation",
          status: "warning",
          threshold: "80%",
          actual: "79%",
          message: "Barely below threshold",
        },
      ],
      evaluated_at: "2026-08-20T10:00:00Z",
    };
    const parsed = qualityGateEvaluationSchema.parse(evaluation);
    expect(parsed.checks).toHaveLength(2);
    expect(parsed.overall_status).toBe("passed");
  });

  it("rejects invalid severity", () => {
    expect(() =>
      securityFindingSchema.parse({
        id: "f1",
        rule_id: "r1",
        tool: "t1",
        category: "sast",
        severity: "super_critical",
        message: "bad",
        file_path: "f.py",
        start_line: 1,
      }),
    ).toThrow();
  });
});
