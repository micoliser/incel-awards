import type { AwardCriterion } from "@/lib/types";

/** Public criteria list — labels only; weights stay committee-only. */
export function CriteriaList({ criteria }: { criteria: AwardCriterion[] }) {
  if (!criteria.length) return null;

  return (
    <ol className="space-y-3">
      {criteria.map((c) => (
        <li
          key={c.label}
          className="border-b border-[var(--rule)] pb-3 text-sm text-ink"
        >
          {c.label}
        </li>
      ))}
    </ol>
  );
}
