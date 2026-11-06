"use client";

type BallotProgressProps = {
  answered: number;
  total: number;
};

export function BallotProgress({ answered, total }: BallotProgressProps) {
  const pct = total === 0 ? 0 : Math.round((answered / total) * 100);

  return (
    <div
      className="border border-[var(--rule)] bg-surface px-4 py-3"
      aria-live="polite"
    >
      <div className="flex items-baseline justify-between gap-3">
        <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
          Ballot progress
        </p>
        <p className="text-sm tabular-nums text-ink">
          {answered} / {total}
        </p>
      </div>
      <div
        className="mt-2 h-1.5 w-full bg-ground-deep"
        role="progressbar"
        aria-valuenow={answered}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`${answered} of ${total} awards answered`}
      >
        <div
          className="h-full bg-indigo transition-[width] duration-300 ease-[var(--ease-out-expo)]"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
