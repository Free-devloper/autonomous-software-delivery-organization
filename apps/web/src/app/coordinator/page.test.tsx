import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CoordinatorPage from "./page";

describe("CoordinatorPage", () => {
  it("renders coordinator page with specialist agent assignments", () => {
    render(<CoordinatorPage />);
    expect(screen.getByText("Coordinator Agent & Specialist Team")).toBeInTheDocument();
    expect(screen.getByText("Autonomous End-to-End Feature Delivery Pipeline")).toBeInTheDocument();
  });

  it("handles trigger pipeline button click", () => {
    render(<CoordinatorPage />);
    const btn = screen.getByTestId("trigger-pipeline-btn");
    fireEvent.click(btn);
  });
});
