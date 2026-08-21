import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SecurityPage from "./page";

describe("SecurityPage", () => {
  it("renders the security page heading", () => {
    render(<SecurityPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: /Security & Quality Gates/i }),
    ).toBeInTheDocument();
  });

  it("displays summary stats cards", () => {
    render(<SecurityPage />);
    expect(screen.getByText("Total Findings")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("Gate Status")).toBeInTheDocument();
  });

  it("shows the security dashboard component", () => {
    render(<SecurityPage />);
    expect(screen.getByTestId("security-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("overall-gate-status")).toBeInTheDocument();
  });
});
