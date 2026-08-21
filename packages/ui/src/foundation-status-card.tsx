export type FoundationStatus = "in-progress" | "ready" | "blocked";

export interface FoundationStatusCardProps {
  readonly status: FoundationStatus;
  readonly updatedAt: string;
}

const statusCopy: Record<FoundationStatus, string> = {
  "in-progress": "Engineering foundation in progress",
  ready: "Engineering foundation ready",
  blocked: "Engineering foundation blocked",
};

const statusClassNames: Record<FoundationStatus, string> = {
  "in-progress": "bg-amber-100 text-amber-950 ring-amber-300",
  ready: "bg-emerald-100 text-emerald-950 ring-emerald-300",
  blocked: "bg-red-100 text-red-950 ring-red-300",
};

/**
 * Announces the current engineering-foundation state without relying on colour
 * alone. Consumers should pass an ISO-8601 timestamp for the latest update.
 */
export function FoundationStatusCard({ status, updatedAt }: FoundationStatusCardProps) {
  return (
    <section
      aria-labelledby="foundation-status-heading"
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="foundation-status-heading" className="text-lg font-semibold text-slate-950">
          Engineering foundation
        </h2>
        <p
          aria-live="polite"
          className={`rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${statusClassNames[status]}`}
          role="status"
        >
          {statusCopy[status]}
        </p>
      </div>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-700">
        The workspace is being prepared for secure, repeatable delivery. Product workflows are not
        available during this foundation phase.
      </p>
      <p className="mt-4 text-sm text-slate-600">
        <span className="font-medium text-slate-800">Last updated: </span>
        <time dateTime={updatedAt}>{updatedAt}</time>
      </p>
    </section>
  );
}
