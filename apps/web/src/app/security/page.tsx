"use client";

import type { QualityGateEvaluation, SecurityFinding, SecurityScanReport } from "@asdo/contracts";
import { SecurityDashboard } from "@asdo/ui";
import React, { useState } from "react";

// Demo scan report with realistic findings
const demoFindings: SecurityFinding[] = [
  {
    id: "finding-0001",
    rule_id: "B101",
    tool: "asdo-sast",
    category: "sast",
    severity: "medium",
    message: "Use of assert detected in production code",
    file_path: "services/api/src/auth/session.py",
    start_line: 42,
    snippet: "assert user.is_active, 'User must be active'",
    cwe_ids: ["CWE-703"],
    suppressed: false,
  },
  {
    id: "finding-0002",
    rule_id: "B102",
    tool: "asdo-sast",
    category: "sast",
    severity: "high",
    message: "Use of exec() detected",
    file_path: "services/api/src/sandbox/runtime.py",
    start_line: 88,
    snippet: "exec(generated_code)",
    cwe_ids: ["CWE-95"],
    suppressed: false,
  },
  {
    id: "finding-0003",
    rule_id: "CVE-2026-1234",
    tool: "asdo-deps",
    category: "dependency",
    severity: "critical",
    message: "Known remote code execution vulnerability in dependency",
    file_path: "requirements.txt",
    start_line: 15,
    cwe_ids: ["CWE-502"],
    suppressed: false,
  },
];

const demoScanReports: SecurityScanReport[] = [
  {
    id: "scan-sast-001",
    organization_id: "018f0000-0000-7000-8000-000000000001",
    scan_target: "services/api",
    tool_name: "asdo-sast",
    tool_version: "1.0.0",
    category: "sast",
    findings: demoFindings.filter((f) => f.category === "sast"),
    total_findings: 2,
    critical_count: 0,
    high_count: 1,
    passed: false,
    scanned_at: new Date().toISOString(),
  },
  {
    id: "scan-deps-001",
    organization_id: "018f0000-0000-7000-8000-000000000001",
    scan_target: "services/api",
    tool_name: "asdo-deps",
    tool_version: "1.0.0",
    category: "dependency",
    findings: demoFindings.filter((f) => f.category === "dependency"),
    total_findings: 1,
    critical_count: 1,
    high_count: 0,
    passed: false,
    scanned_at: new Date().toISOString(),
  },
  {
    id: "scan-secrets-001",
    organization_id: "018f0000-0000-7000-8000-000000000001",
    scan_target: ".",
    tool_name: "asdo-secret-scanner",
    tool_version: "1.0.0",
    category: "secret",
    findings: [],
    total_findings: 0,
    critical_count: 0,
    high_count: 0,
    passed: true,
    scanned_at: new Date().toISOString(),
  },
];

const demoQualityGate: QualityGateEvaluation = {
  id: "qg-demo-001",
  organization_id: "018f0000-0000-7000-8000-000000000001",
  work_package_id: "wp-auth-001",
  overall_status: "failed",
  checks: [
    {
      name: "test_pass_rate",
      status: "passed",
      threshold: "0 failures",
      actual: "0 failures",
    },
    {
      name: "flaky_test_limit",
      status: "passed",
      threshold: "<= 3",
      actual: "1",
    },
    {
      name: "line_coverage",
      status: "passed",
      threshold: ">= 90%",
      actual: "91.9%",
    },
    {
      name: "mutation_score",
      status: "warning",
      threshold: ">= 80%",
      actual: "78.5%",
      message: "Marginally below threshold — review survived mutants",
    },
    {
      name: "critical_findings",
      status: "failed",
      threshold: "<= 0",
      actual: "1",
      message: "CVE-2026-1234 in requirements.txt",
    },
    {
      name: "high_findings",
      status: "failed",
      threshold: "<= 0",
      actual: "1",
    },
  ],
  evaluated_at: new Date().toISOString(),
};

export default function SecurityPage() {
  const [scanReports] = useState<SecurityScanReport[]>(demoScanReports);
  const [qualityGate] = useState<QualityGateEvaluation>(demoQualityGate);

  const gateStatusColorMap: Record<string, string> = {
    passed: "text-emerald-400",
    warning: "text-amber-400",
    failed: "text-rose-400",
  };
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- all gate statuses are in the map
  const gateColor: string = gateStatusColorMap[qualityGate.overall_status]!;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 md:p-10">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Page Header */}
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            Security & Quality Gates
          </h1>
          <p className="text-sm text-slate-400">
            SAST, dependency, secret scanning findings and automated quality gate evaluation for
            work packages.
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            {
              label: "Total Findings",
              value: scanReports.reduce((a, r) => a + r.total_findings, 0),
              color: "text-orange-400",
            },
            {
              label: "Critical",
              value: scanReports.reduce((a, r) => a + r.critical_count, 0),
              color: "text-red-400",
            },
            {
              label: "High",
              value: scanReports.reduce((a, r) => a + r.high_count, 0),
              color: "text-orange-400",
            },
            {
              label: "Gate Status",
              value: qualityGate.overall_status.toUpperCase(),
              color: gateColor,
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col gap-1 rounded-xl border border-slate-800 bg-slate-900/60 p-4"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {stat.label}
              </span>
              <span className={`text-2xl font-black ${stat.color}`}>{String(stat.value)}</span>
            </div>
          ))}
        </div>

        {/* Security Dashboard Component */}
        <SecurityDashboard scanReports={scanReports} qualityGate={qualityGate} />
      </div>
    </div>
  );
}
