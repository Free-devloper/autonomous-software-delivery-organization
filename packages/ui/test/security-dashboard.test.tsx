import type { QualityGateEvaluation, SecurityScanReport } from "@asdo/contracts";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SecurityDashboard } from "../src/security-dashboard";

const dummyScanReport: SecurityScanReport = {
  id: "scan-001",
  organization_id: "018f0000-0000-7000-8000-000000000001",
  scan_target: "services/api",
  tool_name: "asdo-sast",
  tool_version: "1.0.0",
  category: "sast",
  findings: [
    {
      id: "finding-0001",
      rule_id: "B101",
      tool: "asdo-sast",
      category: "sast",
      severity: "medium",
      message: "Use of assert detected.",
      file_path: "src/auth.py",
      start_line: 42,
      cwe_ids: [],
      suppressed: false,
    },
  ],
  total_findings: 1,
  critical_count: 0,
  high_count: 0,
  passed: true,
  scanned_at: "2026-08-20T10:00:00Z",
};

const dummyGateEvaluation: QualityGateEvaluation = {
  id: "qg-001",
  organization_id: "018f0000-0000-7000-8000-000000000001",
  work_package_id: "wp-001",
  overall_status: "passed",
  checks: [
    { name: "test_pass_rate", status: "passed", threshold: "0 failures", actual: "0 failures" },
    { name: "line_coverage", status: "passed", threshold: ">= 90%", actual: "92.0%" },
    {
      name: "mutation_score",
      status: "warning",
      threshold: ">= 80%",
      actual: "79.5%",
      message: "Below threshold",
    },
  ],
  evaluated_at: "2026-08-20T10:00:00Z",
};

describe("SecurityDashboard", () => {
  it("renders the dashboard with scan reports and quality gate", () => {
    render(<SecurityDashboard scanReports={[dummyScanReport]} qualityGate={dummyGateEvaluation} />);

    expect(screen.getByTestId("security-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("overall-gate-status")).toHaveTextContent("passed");
    expect(screen.getByTestId("quality-gate-checks")).toBeInTheDocument();
    expect(screen.getByTestId("gate-check-test_pass_rate")).toBeInTheDocument();
    expect(screen.getByTestId("gate-check-line_coverage")).toBeInTheDocument();
  });

  it("displays findings in the findings table", () => {
    render(<SecurityDashboard scanReports={[dummyScanReport]} qualityGate={null} />);

    expect(screen.getByTestId("findings-table")).toBeInTheDocument();
    expect(screen.getByTestId("finding-finding-0001")).toBeInTheDocument();
    expect(screen.getByText("Use of assert detected.")).toBeInTheDocument();
    expect(screen.getByText("B101")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<SecurityDashboard scanReports={[]} qualityGate={null} />);

    expect(
      screen.getByText("No security scans or quality gate evaluations available yet."),
    ).toBeInTheDocument();
  });

  it("switches scan report tabs", () => {
    const secondReport: SecurityScanReport = {
      ...dummyScanReport,
      id: "scan-002",
      tool_name: "asdo-deps",
      findings: [],
      total_findings: 0,
    };

    render(<SecurityDashboard scanReports={[dummyScanReport, secondReport]} qualityGate={null} />);

    const secondTab = screen.getByTestId("scan-tab-1");
    fireEvent.click(secondTab);

    expect(screen.getByText("No findings detected. ✓")).toBeInTheDocument();
  });
});
