import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ReviewsPage from "./page";

describe("ReviewsPage", () => {
  it("renders the reviews page heading", () => {
    render(<ReviewsPage />);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /Code Reviews & Pull Requests/i,
      }),
    ).toBeInTheDocument();
  });

  it("displays summary stats", () => {
    render(<ReviewsPage />);
    expect(screen.getByText("Total PRs")).toBeInTheDocument();
    expect(screen.getByText("Open")).toBeInTheDocument();
    expect(screen.getByText("Merged")).toBeInTheDocument();
    expect(screen.getByText("Pending Review")).toBeInTheDocument();
  });

  it("renders the review dashboard component", () => {
    render(<ReviewsPage />);
    expect(screen.getByTestId("review-dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("pr-list")).toBeInTheDocument();
  });
});
