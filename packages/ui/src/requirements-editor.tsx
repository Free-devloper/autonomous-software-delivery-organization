"use client";

import { useState } from "react";
import type { ClarificationRequest, RequirementRevision } from "@asdo/contracts";

export interface RequirementsEditorProps {
  currentRevision: RequirementRevision;
  historicalRevisions?: RequirementRevision[];
  clarifications?: ClarificationRequest[];
  onResolveClarification?: (clarificationId: string, response: string) => void;
  onCreateRevision?: (title: string, description: string) => void;
}

export function RequirementsEditor({
  currentRevision,
  historicalRevisions = [],
  clarifications = [],
  onResolveClarification,
  onCreateRevision,
}: RequirementsEditorProps) {
  const [viewingRevisionId, setViewingRevisionId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isCreatingRevision, setIsCreatingRevision] = useState(false);
  const [newTitle, setNewTitle] = useState(currentRevision.title);
  const [newDesc, setNewDesc] = useState(currentRevision.description);

  const selectedRevision: RequirementRevision =
    (viewingRevisionId ? historicalRevisions.find((r) => r.id === viewingRevisionId) : undefined) ??
    currentRevision;

  const pendingClarifications = clarifications.filter((c) => c.status === "pending");

  const handleAnswerSubmit = (clarId: string) => {
    const ans = answers[clarId];
    if (ans && onResolveClarification) {
      onResolveClarification(clarId, ans);
      setAnswers((prev) => ({ ...prev, [clarId]: "" }));
    }
  };

  const handleSaveRevision = () => {
    if (onCreateRevision && newTitle.trim()) {
      onCreateRevision(newTitle, newDesc);
      setViewingRevisionId(null);
      setIsCreatingRevision(false);
    }
  };

  return (
    <div
      data-testid="requirements-editor"
      className="flex flex-col gap-6 rounded-xl border border-slate-800 bg-slate-900/90 p-6 text-slate-100 shadow-xl backdrop-blur"
    >
      {/* Header with Title, Version, and Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-100">{selectedRevision.title}</h2>
            <span
              data-testid="status-badge"
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                selectedRevision.status === "approved"
                  ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                  : selectedRevision.status === "pending_clarification"
                    ? "bg-amber-950/80 text-amber-400 border border-amber-800"
                    : "bg-indigo-950/80 text-indigo-400 border border-indigo-800"
              }`}
            >
              {selectedRevision.status.replace("_", " ")}
            </span>
            <span
              data-testid="version-badge"
              className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-300"
            >
              v{selectedRevision.version}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">{selectedRevision.description}</p>
        </div>

        <div className="flex items-center gap-2">
          {onCreateRevision && (
            <button
              data-testid="new-revision-btn"
              onClick={() => {
                setIsCreatingRevision(!isCreatingRevision);
              }}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-indigo-500"
            >
              {isCreatingRevision ? "Cancel" : "New Revision"}
            </button>
          )}
        </div>
      </div>

      {/* New Revision Form */}
      {isCreatingRevision && (
        <div
          data-testid="new-revision-form"
          className="flex flex-col gap-3 rounded-lg border border-indigo-900/50 bg-indigo-950/20 p-4"
        >
          <h3 className="text-sm font-semibold text-indigo-300">Create New Revision</h3>
          <input
            data-testid="revision-title-input"
            type="text"
            value={newTitle}
            onChange={(e) => {
              setNewTitle(e.target.value);
            }}
            placeholder="Revision Title"
            className="rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <textarea
            data-testid="revision-desc-input"
            value={newDesc}
            onChange={(e) => {
              setNewDesc(e.target.value);
            }}
            placeholder="Revision Description"
            rows={2}
            className="rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            data-testid="save-revision-btn"
            onClick={handleSaveRevision}
            className="self-start rounded bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
          >
            Save Revision
          </button>
        </div>
      )}

      {/* Pending Clarifications Banner */}
      {pendingClarifications.length > 0 && (
        <div
          data-testid="clarifications-banner"
          className="flex flex-col gap-3 rounded-lg border border-amber-900/60 bg-amber-950/30 p-4"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-amber-300">
              Pending Clarification ({pendingClarifications.length})
            </span>
          </div>
          {pendingClarifications.map((clar) => (
            <div
              key={clar.id}
              data-testid={`clarification-${clar.id}`}
              className="flex flex-col gap-2 rounded border border-amber-900/40 bg-slate-950/80 p-3"
            >
              <p className="text-sm text-slate-200">{clar.question}</p>
              {clar.options.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {clar.options.map((opt) => (
                    <button
                      key={opt}
                      onClick={() => {
                        setAnswers((prev) => ({ ...prev, [clar.id]: opt }));
                      }}
                      className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 text-xs text-slate-300 hover:border-amber-600"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}
              <div className="mt-1 flex gap-2">
                <input
                  data-testid={`clarification-input-${clar.id}`}
                  type="text"
                  value={answers[clar.id] ?? ""}
                  onChange={(e) => {
                    setAnswers((prev) => ({ ...prev, [clar.id]: e.target.value }));
                  }}
                  placeholder="Type or select answer..."
                  className="flex-1 rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
                />
                <button
                  data-testid={`clarification-submit-${clar.id}`}
                  onClick={() => {
                    handleAnswerSubmit(clar.id);
                  }}
                  className="rounded bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-500"
                >
                  Submit Answer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Acceptance Criteria */}
      <div className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Acceptance Criteria ({selectedRevision.acceptance_criteria.length})
        </h3>
        <div className="flex flex-col gap-2">
          {selectedRevision.acceptance_criteria.map((ac) => (
            <div
              key={ac.id}
              data-testid={`criterion-${ac.id}`}
              className="flex items-start justify-between gap-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3"
            >
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-emerald-500">✓</span>
                <span className="text-sm text-slate-200">{ac.criterion_text}</span>
              </div>
              <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                {ac.verification_method}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Historical Revisions Selector */}
      {historicalRevisions.length > 1 && (
        <div className="flex flex-col gap-2 border-t border-slate-800 pt-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Revision History
          </h4>
          <div className="flex flex-wrap gap-2">
            {historicalRevisions.map((rev) => (
              <button
                key={rev.id}
                data-testid={`rev-btn-v${rev.version.toString()}`}
                onClick={() => {
                  setViewingRevisionId(rev.id);
                }}
                className={`rounded px-2.5 py-1 text-xs font-mono transition ${
                  selectedRevision.id === rev.id
                    ? "bg-indigo-600 text-white font-bold"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                v{rev.version} ({rev.status})
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
