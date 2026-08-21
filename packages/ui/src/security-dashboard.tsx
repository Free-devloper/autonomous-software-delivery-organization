"use client";

import type { QualityGateEvaluation, SecurityScanReport } from "@asdo/contracts";
import React, { useState } from "react";

export interface SecurityDashboardProps {
  scanReports: SecurityScanReport[];
  qualityGate: QualityGateEvaluation | null;
}

const severityColors: Record<string, string> = {
  critical: "bg-red-950/60 text-red-300 border-red-800/40",
  high: "bg-orange-950/60 text-orange-300 border-orange-800/40",
  medium: "bg-amber-950/60 text-amber-300 border-amber-800/40",
  low: "bg-sky-950/60 text-sky-300 border-sky-800/40",
  informational: "bg-slate-800/60 text-slate-300 border-slate-700/40",
};

const gateStatusColors: Record<string, string> = {
  passed: "bg-emerald-950/60 text-emerald-300 border-emerald-800/40",
  failed: "bg-rose-950/60 text-rose-300 border-rose-800/40",
  warning: "bg-amber-950/60 text-amber-300 border-amber-800/40",
};

export const SecurityDashboard: React.FC<SecurityDashboardProps> = ({
  scanReports,
  qualityGate,
}) => {
  const [selectedReportIdx, setSelectedReportIdx] = useState(0);
  const selectedReport = scanReports[selectedReportIdx] ?? null;

  return (
    <div
      data-testid="security-dashboard"
      className="flex flex-col gap-6 rounded-xl border border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-rose-600 to-orange-600 text-lg font-bold">
            🛡
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">
              Security & Quality Gates
            </h2>
            <p className="text-xs text-slate-400">
              {String(scanReports.length)} scan report
              {scanReports.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>

        {qualityGate && (
          <span
            data-testid="overall-gate-status"
            className={`rounded-lg px-4 py-2 text-sm font-bold uppercase border ${
              gateStatusColors[qualityGate.overall_status] ?? ""
            }`}
          >
            {qualityGate.overall_status}
          </span>
        )}
      </div>

      {/* Quality Gate Checks */}
      {qualityGate && qualityGate.checks.length > 0 && (
        <div data-testid="quality-gate-checks" className="flex flex-col gap-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Quality Gate Checks
          </h3>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {qualityGate.checks.map((check) => (
              <div
                key={check.name}
                data-testid={`gate-check-${check.name}`}
                className={`flex flex-col gap-1 rounded-lg border p-3 ${
                  gateStatusColors[check.status] ?? ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase">{check.name}</span>
                  <span className="text-[10px] font-bold uppercase">{check.status}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span>Threshold: {check.threshold}</span>
                  <span className="text-slate-300">|</span>
                  <span>Actual: {check.actual}</span>
                </div>
                {check.message && <p className="text-[10px] italic opacity-80">{check.message}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scan Report Tabs */}
      {scanReports.length > 0 && (
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Scan Reports
          </h3>
          <div className="flex gap-2 overflow-x-auto border-b border-slate-800/60 pb-2">
            {scanReports.map((report, idx) => (
              <button
                key={report.id}
                type="button"
                data-testid={`scan-tab-${String(idx)}`}
                onClick={() => {
                  setSelectedReportIdx(idx);
                }}
                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  selectedReportIdx === idx
                    ? "bg-slate-800 text-cyan-300 shadow-sm border border-cyan-500/30"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold border ${
                    report.passed
                      ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/40"
                      : "bg-rose-950/60 text-rose-300 border-rose-800/40"
                  }`}
                >
                  {report.passed ? "PASS" : "FAIL"}
                </span>
                <span className="font-mono">{report.tool_name}</span>
                <span className="text-slate-500">({String(report.total_findings)})</span>
              </button>
            ))}
          </div>

          {/* Findings Table */}
          {selectedReport && (
            <div
              data-testid="findings-table"
              className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900/60"
            >
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2 text-xs font-mono text-slate-400 bg-slate-900">
                <span>
                  {selectedReport.tool_name} v{selectedReport.tool_version} —{" "}
                  {selectedReport.scan_target}
                </span>
                <span>
                  {String(selectedReport.total_findings)} finding
                  {selectedReport.total_findings !== 1 ? "s" : ""}
                </span>
              </div>
              {selectedReport.findings.length === 0 ? (
                <div className="p-4 text-sm text-emerald-400 italic">No findings detected. ✓</div>
              ) : (
                <div className="divide-y divide-slate-800/60">
                  {selectedReport.findings.map((finding) => (
                    <div
                      key={finding.id}
                      data-testid={`finding-${finding.id}`}
                      className="flex items-start gap-3 p-3 text-xs"
                    >
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold border whitespace-nowrap ${
                          severityColors[finding.severity] ?? ""
                        }`}
                      >
                        {finding.severity}
                      </span>
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-white">{finding.rule_id}</span>
                          <span className="text-slate-300">{finding.message}</span>
                        </div>
                        <div className="font-mono text-slate-500">
                          {finding.file_path}:{String(finding.start_line)}
                        </div>
                        {finding.snippet && (
                          <code className="mt-1 rounded bg-slate-800/60 px-2 py-1 text-[10px] text-slate-300">
                            {finding.snippet}
                          </code>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {scanReports.length === 0 && !qualityGate && (
        <div className="text-center text-sm text-slate-500 py-8">
          No security scans or quality gate evaluations available yet.
        </div>
      )}
    </div>
  );
};
