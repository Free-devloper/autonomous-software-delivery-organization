import { FoundationStatusCard } from "@asdo/ui";

const foundationUpdatedAt = "2026-08-18T00:00:00Z";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl items-center px-6 py-12 sm:px-10">
      <div className="w-full">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-sky-800">
          Autonomous Software Delivery Organization
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
          Building the delivery foundation
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-700">
          This environment is intentionally limited while engineering foundations are established
          and verified.
        </p>
        <div className="mt-8">
          <FoundationStatusCard status="in-progress" updatedAt={foundationUpdatedAt} />
        </div>
      </div>
    </main>
  );
}
