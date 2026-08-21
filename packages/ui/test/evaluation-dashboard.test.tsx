import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EvaluationDashboard, type MetricItemDisplay } from "../src/evaluation-dashboard";

describe("EvaluationDashboard", () => {
  const mockMetrics: MetricItemDisplay[] = [
    {
      name: "coverage",
      category: "correctness",
      score: 92.5,
      target_threshold: 90.0,
      passed: true,
      unit: "%",
      details: "Branch and line coverage satisfied",
    },
    {
      name: "security_vulnerabilities",
      category: "security_recall",
      score: 1,
      target_threshold: 0,
      passed: false,
      unit: "count",
    },
  ];

  it("renders evaluation status, metrics and cost cards with passing state", () => {
    render(
      <EvaluationDashboard
        status="passed"
        summary="All readiness thresholds met"
        metrics={mockMetrics}
        totalCostUsd={45.2}
        budgetLimitUsd={200.0}
        budgetConsumedPercentage={22.6}
        isWithinBudget={true}
        rpoMinutes={15}
        rtoMinutes={60}
        lastBackupDigest={"a".repeat(64)}
      />,
    );

    expect(screen.getByTestId("evaluation-dashboard")).toBeInTheDocument();
    expect(screen.getByText("All readiness thresholds met")).toBeInTheDocument();
    expect(screen.getByText("$45.20")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("renders warning status with over-budget condition and without backup digest", () => {
    render(
      <EvaluationDashboard
        status="warning"
        summary="Budget breached and warning status"
        metrics={[]}
        totalCostUsd={250.0}
        budgetLimitUsd={200.0}
        budgetConsumedPercentage={125.0}
        isWithinBudget={false}
        rpoMinutes={30}
        rtoMinutes={120}
      />,
    );

    expect(screen.getByText("warning")).toBeInTheDocument();
    expect(screen.getByText("$250.00")).toBeInTheDocument();
  });

  it("triggers evaluation and backup callbacks", () => {
    const onRunEvaluation = vi.fn();
    const onTriggerBackup = vi.fn();

    render(
      <EvaluationDashboard
        status="passed"
        summary="Ready"
        metrics={mockMetrics}
        totalCostUsd={10.0}
        budgetLimitUsd={100.0}
        budgetConsumedPercentage={10.0}
        isWithinBudget={true}
        rpoMinutes={15}
        rtoMinutes={60}
        onRunEvaluation={onRunEvaluation}
        onTriggerBackup={onTriggerBackup}
      />,
    );

    const runBtn = screen.getByTestId("run-evaluation-btn");
    fireEvent.click(runBtn);
    expect(onRunEvaluation).toHaveBeenCalledTimes(1);

    const backupBtn = screen.getByText("Trigger Snapshot");
    fireEvent.click(backupBtn);
    expect(onTriggerBackup).toHaveBeenCalledTimes(1);
  });
});
