import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("truthfully communicates the limited foundation state", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: "Building the delivery foundation" })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Engineering foundation in progress");
    expect(
      screen.getByText(/product workflows are not available during this foundation phase/i),
    ).toBeVisible();
  });
});
