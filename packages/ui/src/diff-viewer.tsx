"use client";

import type { PatchApplicationResult, PatchProposal } from "@asdo/contracts";
import React, { useState } from "react";

export interface DiffViewerProps {
  proposal: PatchProposal;
  onApply?: (proposalId: string) => Promise<PatchApplicationResult | undefined>;
  isApplying?: boolean;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  proposal,
  onApply,
  isApplying = false,
}) => {
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [applyResult, setApplyResult] = useState<PatchApplicationResult | null>(null);

  const selectedFile = proposal.files[selectedFileIndex] ?? proposal.files[0];

  const handleApply = async () => {
    if (!onApply) return;
    try {
      const result = await onApply(proposal.id);
      if (result) {
        setApplyResult(result);
      }
    } catch {
      // Error handled by parent or state
    }
  };

  const getOperationBadge = (op: string) => {
    switch (op) {
      case "add":
        return "bg-emerald-950/60 text-emerald-300 border-emerald-800/40";
      case "delete":
        return "bg-rose-950/60 text-rose-300 border-rose-800/40";
      default:
        return "bg-amber-950/60 text-amber-300 border-amber-800/40";
    }
  };

  return (
    <div
      data-testid="diff-viewer"
      className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-xl"
    >
      {/* Header & Digest */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight text-white">{proposal.summary}</h2>
            <span className="rounded-md bg-cyan-950/60 px-2.5 py-0.5 text-xs font-medium text-cyan-300 border border-cyan-800/40">
              {proposal.work_package_id}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="font-mono text-slate-500">Digest:</span>
            <span
              data-testid="patch-digest"
              className="font-mono text-cyan-400 truncate max-w-md"
              title={proposal.digest_sha256}
            >
              sha256:{proposal.digest_sha256.slice(0, 16)}...
            </span>
          </div>
        </div>

        {onApply && (
          <button
            type="button"
            data-testid="apply-patch-button"
            onClick={() => {
              void handleApply();
            }}
            disabled={isApplying || applyResult?.applied}
            className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white shadow-lg transition-all hover:bg-cyan-500 disabled:opacity-50"
          >
            {isApplying ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Applying...
              </>
            ) : applyResult?.applied ? (
              "✓ Applied"
            ) : (
              "Apply Patch"
            )}
          </button>
        )}
      </div>

      {/* Conflict / Application Result Banner */}
      {applyResult && !applyResult.applied && applyResult.conflicts.length > 0 && (
        <div
          data-testid="merge-conflict-banner"
          className="rounded-lg border border-rose-800/50 bg-rose-950/40 p-4 text-sm text-rose-300"
        >
          <div className="font-semibold text-rose-200">Merge Conflict Detected:</div>
          <ul className="mt-1 list-disc pl-5">
            {applyResult.conflicts.map((c) => (
              <li key={c.path}>
                <span className="font-mono font-medium text-white">{c.path}</span>: {c.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* File Navigation Tabs */}
      <div className="flex gap-2 overflow-x-auto border-b border-slate-800/60 pb-2">
        {proposal.files.map((file, idx) => (
          <button
            key={file.path}
            type="button"
            data-testid={`file-tab-${String(idx)}`}
            onClick={() => {
              setSelectedFileIndex(idx);
            }}
            className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
              selectedFileIndex === idx
                ? "bg-slate-800 text-cyan-300 shadow-sm border border-cyan-500/30"
                : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
            }`}
          >
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold border ${getOperationBadge(
                file.operation,
              )}`}
            >
              {file.operation}
            </span>
            <span className="font-mono">{file.path}</span>
          </button>
        ))}
      </div>

      {/* Diff Content View */}
      {selectedFile && (
        <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2 text-xs font-mono text-slate-400 bg-slate-900">
            <span>{selectedFile.path}</span>
            <span>
              {String(selectedFile.hunks.reduce((acc, h) => acc + h.lines.length, 0))} diff lines
            </span>
          </div>

          <div
            data-testid="diff-lines"
            className="overflow-x-auto p-4 font-mono text-xs leading-relaxed"
          >
            {selectedFile.hunks.length === 0 ? (
              <div className="text-slate-500 italic">No content hunks available.</div>
            ) : (
              selectedFile.hunks.map((hunk, hIdx) => (
                <div key={hIdx} className="mb-4 last:mb-0">
                  <div className="bg-slate-800/40 text-cyan-400/80 px-2 py-0.5 text-[11px] select-none rounded mb-1">
                    @@ -{hunk.old_start},{hunk.old_lines} +{hunk.new_start},{hunk.new_lines} @@
                  </div>
                  {hunk.lines.map((line, lIdx) => {
                    const isAdded = line.startsWith("+");
                    const isRemoved = line.startsWith("-");
                    return (
                      <div
                        key={lIdx}
                        className={`px-2 py-0.5 rounded-sm flex items-start gap-2 ${
                          isAdded
                            ? "bg-emerald-950/40 text-emerald-300 font-medium"
                            : isRemoved
                              ? "bg-rose-950/40 text-rose-300 font-medium"
                              : "text-slate-300"
                        }`}
                      >
                        <span className="select-none text-slate-600 w-4 text-center">
                          {isAdded ? "+" : isRemoved ? "-" : " "}
                        </span>
                        <span className="whitespace-pre">{line.slice(1)}</span>
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
