import type { AwardCriterion } from "@/lib/types";

export function CriteriaList({ criteria }: { criteria: AwardCriterion[] }) {
  if (!criteria.length) return null;

  return (
    <ol className="space-y-3">
      {criteria.map((c) => (
        <li
          key={c.label}
          className="flex items-baseline justify-between gap-4 border-b border-[var(--rule)] pb-3"
        >
          <span className="text-sm text-ink">{c.label}</span>
          <span className="font-[family-name:var(--font-label)] text-xs font-semibold tabular-nums tracking-wide text-indigo">
            {c.weight_percent}%
          </span>
        </li>
      ))}
    </ol>
  );
}
