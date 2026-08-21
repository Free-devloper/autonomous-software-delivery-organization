import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RepositoryBrowser } from "../src/repository-browser";

describe("RepositoryBrowser", () => {
  const sha = "a".repeat(40);
  const sampleEntries = [
    { name: "src", path: "src", type: "directory" as const, size_bytes: 0 },
    { name: "main.ts", path: "src/main.ts", type: "file" as const, size_bytes: 1024 },
  ];

  it("renders repository header and file tree entries", () => {
    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
      />,
    );

    expect(screen.getByText("roytechworkforce/asdo")).toBeVisible();
    expect(screen.getByText("aaaaaaaaaa")).toBeVisible();
    expect(screen.getByText("main.ts")).toBeVisible();
    expect(screen.getByText("src")).toBeVisible();
  });

  it("renders empty directory notice when no entries are present", () => {
    render(
      <RepositoryBrowser repositoryName="roytechworkforce/asdo" commitSha={sha} entries={[]} />,
    );

    expect(screen.getByText("No files in directory")).toBeVisible();
  });

  it("calls onSelectFile when clicking a file entry", () => {
    const handleSelect = vi.fn();
    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        onSelectFile={handleSelect}
      />,
    );

    fireEvent.click(screen.getByText("main.ts"));
    expect(handleSelect).toHaveBeenCalledWith("src/main.ts");
  });

  it("renders active file content with line numbers", () => {
    const activeFile = {
      commit_sha: sha,
      path: "src/main.ts",
      content: "console.log('hello');\nconst x = 42;",
      is_binary: false,
      size_bytes: 35,
      lines_count: 2,
    };

    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        activeFile={activeFile}
      />,
    );

    expect(screen.getByText("src/main.ts")).toBeVisible();
    expect(screen.getByText("console.log('hello');")).toBeVisible();
    expect(screen.getByText("const x = 42;")).toBeVisible();
    expect(screen.getByText("1")).toBeVisible();
    expect(screen.getByText("2")).toBeVisible();
  });

  it("renders binary file notification", () => {
    const binaryFile = {
      commit_sha: sha,
      path: "image.png",
      content: "<binary data>",
      is_binary: true,
      size_bytes: 1200,
      lines_count: 0,
    };

    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        activeFile={binaryFile}
      />,
    );

    expect(screen.getByText("Binary file (1200 bytes)")).toBeVisible();
  });

  it("renders loading and error states", () => {
    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        isLoading={true}
        errorMessage="Network error fetching repository"
      />,
    );

    expect(screen.getByText("Network error fetching repository")).toBeVisible();
    expect(screen.getByText("Loading source...")).toBeVisible();
  });

  it("renders and selects search results", () => {
    const handleSelect = vi.fn();
    const searchResults = {
      commit_sha: sha,
      query: "hello",
      total_matches: 1,
      matches: [
        {
          path: "src/main.ts",
          line_number: 10,
          line_content: "console.log('hello')",
        },
      ],
    };

    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        searchResults={searchResults}
        onSelectFile={handleSelect}
      />,
    );

    expect(screen.getByText("Matches (1)")).toBeVisible();
    expect(screen.getByText("L10: console.log('hello')")).toBeVisible();

    fireEvent.click(screen.getByTestId("match-src/main.ts"));
    expect(handleSelect).toHaveBeenCalledWith("src/main.ts");
  });

  it("triggers onSearch upon submitting search form", () => {
    const handleSearch = vi.fn();
    render(
      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={sha}
        entries={sampleEntries}
        onSearch={handleSearch}
      />,
    );

    const input = screen.getByTestId("search-input");
    fireEvent.change(input, { target: { value: "myquery" } });
    fireEvent.click(screen.getByTestId("search-button"));

    expect(handleSearch).toHaveBeenCalledWith("myquery");
  });
});
