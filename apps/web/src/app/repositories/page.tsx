"use client";

import { useState } from "react";
import type { FileContentResponse, FileEntry, LexicalSearchResult } from "@asdo/contracts";
import { RepositoryBrowser } from "@asdo/ui";

const defaultCommitSha = "e4d909c290d0fb1ca068ffaddf22cbd0adddefec";

const defaultEntries: FileEntry[] = [
  { name: "apps", path: "apps", type: "directory", size_bytes: 0 },
  { name: "packages", path: "packages", type: "directory", size_bytes: 0 },
  { name: "services", path: "services", type: "directory", size_bytes: 0 },
  { name: "package.json", path: "package.json", type: "file", size_bytes: 1420 },
  { name: "README.md", path: "README.md", type: "file", size_bytes: 3200 },
];

const defaultFile: FileContentResponse = {
  commit_sha: defaultCommitSha,
  path: "README.md",
  content: `# Autonomous Software Delivery Organization (ASDO)

Production-grade autonomous software delivery platform.

## Features
- Provider-neutral SCM integration (GitHub & GitLab)
- Immutable commit dereferencing & isolated worktrees
- Real automated verification and deterministic security gates
`,
  is_binary: false,
  size_bytes: 280,
  lines_count: 9,
};

export default function RepositoriesPage() {
  const [activeFile, setActiveFile] = useState<FileContentResponse | null>(defaultFile);
  const [searchResults, setSearchResults] = useState<LexicalSearchResult | null>(null);

  const handleSelectFile = (path: string) => {
    setActiveFile({
      commit_sha: defaultCommitSha,
      path,
      content: `// Source code content for ${path}\nexport const ready = true;\n`,
      is_binary: false,
      size_bytes: 65,
      lines_count: 2,
    });
  };

  const handleSearch = (query: string) => {
    if (!query) {
      setSearchResults(null);
      return;
    }
    setSearchResults({
      commit_sha: defaultCommitSha,
      query,
      total_matches: 1,
      matches: [
        {
          path: "README.md",
          line_number: 1,
          line_content: `# Autonomous Software Delivery Organization (${query})`,
        },
      ],
    });
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-8 sm:px-10">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-500">
          Repository Intelligence
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-white">Repository Explorer</h1>
      </div>

      <RepositoryBrowser
        repositoryName="roytechworkforce/asdo"
        commitSha={defaultCommitSha}
        entries={defaultEntries}
        activeFile={activeFile}
        searchResults={searchResults}
        onSelectFile={handleSelectFile}
        onSearch={handleSearch}
      />
    </main>
  );
}
