import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import EvaluationPage from "./page";

describe("EvaluationPage", () => {
  it("renders production readiness metrics and cost cards", () => {
    render(<EvaluationPage />);
    expect(screen.getByText("Production Readiness & Analytics")).toBeInTheDocument();
    expect(screen.getByText("$102.70")).toBeInTheDocument();
  });

  it("handles run evaluation and backup callbacks", () => {
    render(<EvaluationPage />);
    const runBtn = screen.getByTestId("run-evaluation-btn");
    fireEvent.click(runBtn);

    const backupBtn = screen.getByText("Trigger Snapshot");
    fireEvent.click(backupBtn);
  });
});
