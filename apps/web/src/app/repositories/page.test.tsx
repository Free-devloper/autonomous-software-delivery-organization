import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RepositoriesPage from "./page";

describe("RepositoriesPage", () => {
  it("renders repository explorer with file tree and header", () => {
    render(<RepositoriesPage />);

    expect(screen.getByRole("heading", { name: "Repository Explorer" })).toBeVisible();
    expect(screen.getByText("roytechworkforce/asdo")).toBeVisible();
    expect(screen.getByTestId("file-entry-README.md")).toBeVisible();
    expect(screen.getByTestId("file-entry-package.json")).toBeVisible();
  });

  it("updates active file when clicking a file in the tree", () => {
    render(<RepositoriesPage />);

    fireEvent.click(screen.getByTestId("file-entry-package.json"));
    expect(screen.getAllByText("package.json").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("// Source code content for package.json")).toBeVisible();
  });

  it("triggers search and displays matches, and clears when empty query", () => {
    render(<RepositoriesPage />);

    const input = screen.getByTestId("search-input");
    fireEvent.change(input, { target: { value: "ASDO" } });
    fireEvent.click(screen.getByTestId("search-button"));

    expect(screen.getByText("Matches (1)")).toBeVisible();

    // Clear search
    fireEvent.change(input, { target: { value: "" } });
    fireEvent.click(screen.getByTestId("search-button"));
    expect(screen.queryByText("Matches (1)")).toBeNull();
  });
});
