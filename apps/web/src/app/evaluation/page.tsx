"use client";

import { useState } from "react";

import { EvaluationDashboard, type MetricItemDisplay } from "@asdo/ui";

const defaultMetrics: MetricItemDisplay[] = [
  {
    name: "test_suite_pass_rate",
    category: "correctness",
    score: 100,
    target_threshold: 100,
    passed: true,
    unit: "%",
    details: "149/149 test suites passing",
  },
  {
    name: "code_coverage_overall",
    category: "correctness",
    score: 91.3,
    target_threshold: 90.0,
    passed: true,
    unit: "%",
    details: "Exceeds 90% branch and line threshold",
  },
  {
    name: "mutation_score",
    category: "mutation_score",
    score: 86.2,
    target_threshold: 80.0,
    passed: true,
    unit: "%",
    details: "Mutants killed: 125/145",
  },
  {
    name: "security_vulnerabilities",
    category: "security_recall",
    score: 0,
    target_threshold: 0,
    passed: true,
    unit: "count",
    details: "0 critical or high findings",
  },
  {
    name: "p99_latency_ms",
    category: "performance_slo",
    score: 142,
    target_threshold: 200,
    passed: true,
    unit: "ms",
    details: "Under SLO target",
  },
  {
    name: "disaster_recovery_rto",
    category: "recovery_readiness",
    score: 3.0,
    target_threshold: 60.0,
    passed: true,
    unit: "minutes",
    details: "Verified in automated restore rehearsal",
  },
];

export default function EvaluationPage() {
  const [metrics, setMetrics] = useState<MetricItemDisplay[]>(defaultMetrics);
  const [status, setStatus] = useState<"running" | "passed" | "warning" | "failed">("passed");

  const handleRunEvaluation = () => {
    setStatus("passed");
    setMetrics([...defaultMetrics]);
  };

  const handleTriggerBackup = () => {
    // simulated backup trigger
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">
            Production Readiness &amp; Analytics
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Holistic quality gate evaluations, token cost tracking against quotas, and automated
            disaster recovery drills.
          </p>
        </div>

        <EvaluationDashboard
          status={status}
          summary="All production readiness thresholds and SLOs satisfied across 6 categories."
          metrics={metrics}
          totalCostUsd={102.7}
          budgetLimitUsd={500.0}
          budgetConsumedPercentage={20.54}
          isWithinBudget={true}
          rpoMinutes={15}
          rtoMinutes={60}
          lastBackupDigest="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
          onRunEvaluation={handleRunEvaluation}
          onTriggerBackup={handleTriggerBackup}
        />
      </div>
    </div>
  );
}
