import { z } from "zod";

/** Severity level for security findings (SARIF-aligned). */
export const findingSeveritySchema = z.enum(["critical", "high", "medium", "low", "informational"]);
export type FindingSeverity = z.infer<typeof findingSeveritySchema>;

/** Category of a security scan tool. */
export const scanToolCategorySchema = z.enum([
  "sast",
  "dependency",
  "secret",
  "container",
  "iac",
  "license",
]);
export type ScanToolCategory = z.infer<typeof scanToolCategorySchema>;

/** Individual security finding in SARIF-compatible format. */
export const securityFindingSchema = z
  .object({
    id: z.string().min(1),
    rule_id: z.string().min(1),
    tool: z.string().min(1),
    category: scanToolCategorySchema,
    severity: findingSeveritySchema,
    message: z.string().min(1),
    file_path: z.string().min(1),
    start_line: z.number().int().nonnegative(),
    end_line: z.number().int().nonnegative().optional(),
    snippet: z.string().optional(),
    cwe_ids: z.array(z.string()).default([]),
    fix_suggestion: z.string().optional(),
    suppressed: z.boolean().default(false),
  })
  .strict();
export type SecurityFinding = z.infer<typeof securityFindingSchema>;

/** Aggregated security scan report. */
export const securityScanReportSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    scan_target: z.string().min(1),
    tool_name: z.string().min(1),
    tool_version: z.string().min(1),
    category: scanToolCategorySchema,
    findings: z.array(securityFindingSchema),
    total_findings: z.number().int().nonnegative(),
    critical_count: z.number().int().nonnegative(),
    high_count: z.number().int().nonnegative(),
    passed: z.boolean(),
    scanned_at: z.iso.datetime(),
  })
  .strict();
export type SecurityScanReport = z.infer<typeof securityScanReportSchema>;

/** Test execution status. */
export const testStatusSchema = z.enum(["passed", "failed", "skipped", "error", "flaky"]);
export type TestStatus = z.infer<typeof testStatusSchema>;

/** Single test case result. */
export const testCaseResultSchema = z
  .object({
    id: z.string().min(1),
    name: z.string().min(1),
    suite: z.string().min(1),
    file_path: z.string().min(1),
    status: testStatusSchema,
    duration_ms: z.number().nonnegative(),
    error_message: z.string().optional(),
    retry_count: z.number().int().nonnegative().default(0),
    is_flaky: z.boolean().default(false),
  })
  .strict();
export type TestCaseResult = z.infer<typeof testCaseResultSchema>;

/** Coverage report for a module or file. */
export const coverageEntrySchema = z
  .object({
    file_path: z.string().min(1),
    statement_coverage: z.number().min(0).max(100),
    branch_coverage: z.number().min(0).max(100),
    function_coverage: z.number().min(0).max(100),
    line_coverage: z.number().min(0).max(100),
    uncovered_lines: z.array(z.number().int().nonnegative()).default([]),
  })
  .strict();
export type CoverageEntry = z.infer<typeof coverageEntrySchema>;

/** Mutation testing result for a single mutant. */
export const mutationResultSchema = z.enum(["killed", "survived", "timeout", "no_coverage"]);
export type MutationResult = z.infer<typeof mutationResultSchema>;

/** Mutation testing summary. */
export const mutationReportSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    total_mutants: z.number().int().nonnegative(),
    killed: z.number().int().nonnegative(),
    survived: z.number().int().nonnegative(),
    timeout: z.number().int().nonnegative(),
    no_coverage: z.number().int().nonnegative(),
    mutation_score: z.number().min(0).max(100),
    threshold: z.number().min(0).max(100),
    passed: z.boolean(),
    generated_at: z.iso.datetime(),
  })
  .strict();
export type MutationReport = z.infer<typeof mutationReportSchema>;

/** Aggregated test suite run report. */
export const testSuiteReportSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    suite_name: z.string().min(1),
    total_tests: z.number().int().nonnegative(),
    passed: z.number().int().nonnegative(),
    failed: z.number().int().nonnegative(),
    skipped: z.number().int().nonnegative(),
    flaky: z.number().int().nonnegative(),
    duration_ms: z.number().nonnegative(),
    coverage: z.array(coverageEntrySchema).default([]),
    test_results: z.array(testCaseResultSchema).default([]),
    overall_passed: z.boolean(),
    run_at: z.iso.datetime(),
  })
  .strict();
export type TestSuiteReport = z.infer<typeof testSuiteReportSchema>;

/** Quality gate evaluation result. */
export const qualityGateStatusSchema = z.enum(["passed", "failed", "warning"]);
export type QualityGateStatus = z.infer<typeof qualityGateStatusSchema>;

/** Individual quality gate check. */
export const qualityGateCheckSchema = z
  .object({
    name: z.string().min(1),
    status: qualityGateStatusSchema,
    threshold: z.string().min(1),
    actual: z.string().min(1),
    message: z.string().optional(),
  })
  .strict();
export type QualityGateCheck = z.infer<typeof qualityGateCheckSchema>;

/** Combined quality gate evaluation. */
export const qualityGateEvaluationSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    work_package_id: z.string().min(1),
    overall_status: qualityGateStatusSchema,
    checks: z.array(qualityGateCheckSchema),
    evaluated_at: z.iso.datetime(),
  })
  .strict();
export type QualityGateEvaluation = z.infer<typeof qualityGateEvaluationSchema>;
