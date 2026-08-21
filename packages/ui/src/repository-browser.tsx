"use client";

import React, { useState } from "react";
import type {
  FileContentResponse,
  FileEntry,
  LexicalSearchMatch,
  LexicalSearchResult,
} from "@asdo/contracts";

export interface RepositoryBrowserProps {
  repositoryName: string;
  commitSha: string;
  entries: FileEntry[];
  activeFile?: FileContentResponse | null;
  searchResults?: LexicalSearchResult | null;
  onSelectFile?: (path: string) => void;
  onSearch?: (query: string) => void;
  isLoading?: boolean;
  errorMessage?: string | null;
}

export function RepositoryBrowser({
  repositoryName,
  commitSha,
  entries,
  activeFile,
  searchResults,
  onSelectFile,
  onSearch,
  isLoading = false,
  errorMessage = null,
}: RepositoryBrowserProps): React.JSX.Element {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearchSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchQuery);
    }
  };

  return (
    <div
      className="flex flex-col h-[700px] w-full rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-100 shadow-2xl overflow-hidden font-sans"
      data-testid="repository-browser"
    >
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-neutral-800 bg-neutral-900/60 backdrop-blur">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-lg text-white">{repositoryName}</span>
          <span className="text-xs px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 font-mono">
            {commitSha.slice(0, 10)}
          </span>
        </div>
        <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Search code..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setSearchQuery(e.target.value);
            }}
            className="px-3 py-1.5 text-sm bg-neutral-800 border border-neutral-700 rounded-lg text-white placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            data-testid="search-input"
          />
          <button
            type="submit"
            className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 font-medium rounded-lg text-white transition-colors"
            data-testid="search-button"
          >
            Search
          </button>
        </form>
      </header>

      {/* Error Alert */}
      {errorMessage && (
        <div className="px-6 py-3 bg-red-950/60 border-b border-red-800/80 text-red-300 text-sm flex items-center justify-between">
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar: File Tree & Search Results */}
        <aside className="w-80 border-r border-neutral-800 bg-neutral-900/30 flex flex-col overflow-y-auto">
          {searchResults && searchResults.matches.length > 0 ? (
            <div className="p-4 space-y-2">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                Matches ({searchResults.total_matches})
              </h2>
              <div className="space-y-1">
                {searchResults.matches.map((m: LexicalSearchMatch, idx: number) => (
                  <button
                    key={`${m.path}-${m.line_number.toString()}-${idx.toString()}`}
                    type="button"
                    onClick={() => onSelectFile?.(m.path)}
                    className="w-full text-left p-2 rounded hover:bg-neutral-800 text-xs transition-colors"
                    data-testid={`match-${m.path}`}
                  >
                    <div className="font-mono text-blue-400 font-medium">{m.path}</div>
                    <div className="text-neutral-400 text-[11px] truncate">
                      L{m.line_number}: {m.line_content}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-1">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">
                Files
              </h2>
              {entries.length === 0 ? (
                <p className="text-sm text-neutral-500 italic">No files in directory</p>
              ) : (
                entries.map((entry: FileEntry) => (
                  <button
                    key={entry.path}
                    type="button"
                    onClick={() => onSelectFile?.(entry.path)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left ${
                      activeFile?.path === entry.path
                        ? "bg-blue-600/20 text-blue-300 font-medium"
                        : "hover:bg-neutral-800/60 text-neutral-300"
                    }`}
                    data-testid={`file-entry-${entry.name}`}
                  >
                    <span className="truncate">{entry.name}</span>
                    {entry.type === "directory" ? (
                      <span className="text-xs text-neutral-500">dir</span>
                    ) : (
                      <span className="text-xs text-neutral-500">
                        {(entry.size_bytes / 1024).toFixed(1)}k
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          )}
        </aside>

        {/* Right Pane: Code Viewer */}
        <main className="flex-1 flex flex-col overflow-hidden bg-neutral-950">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center text-neutral-400 text-sm">
              Loading source...
            </div>
          ) : activeFile ? (
            <div className="flex flex-col h-full">
              {/* File Info Bar */}
              <div className="flex items-center justify-between px-6 py-2 border-b border-neutral-800/80 bg-neutral-900/20 text-xs text-neutral-400 font-mono">
                <span>{activeFile.path}</span>
                <span>
                  {activeFile.lines_count} lines • {activeFile.size_bytes} bytes
                </span>
              </div>
              {/* Code Lines */}
              <div className="flex-1 overflow-auto p-4 font-mono text-sm leading-relaxed text-neutral-200">
                {activeFile.is_binary ? (
                  <div className="flex items-center justify-center h-full text-neutral-500 italic">
                    Binary file ({activeFile.size_bytes} bytes)
                  </div>
                ) : (
                  <table className="w-full border-collapse">
                    <tbody>
                      {activeFile.content.split("\n").map((line: string, idx: number) => (
                        <tr key={idx} className="hover:bg-neutral-900/40">
                          <td className="w-12 text-right pr-4 text-neutral-600 select-none text-xs">
                            {idx + 1}
                          </td>
                          <td className="whitespace-pre font-mono text-neutral-300">{line}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-neutral-500 text-sm">
              Select a file to inspect its content
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
