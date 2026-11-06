import { yearStatusLabel } from "@/lib/format";
import type { YearStatus } from "@/lib/types";

const STATUS_TONE: Record<YearStatus, string> = {
  draft: "bg-ground-deep text-ink-muted ring-1 ring-[var(--rule)]",
  scheduled:
    "bg-[color-mix(in_srgb,var(--gold)_22%,var(--surface))] text-gold-bright ring-1 ring-gold/40",
  voting: "bg-teal text-ground ring-1 ring-teal/50",
  closed: "bg-indigo text-ink ring-1 ring-indigo/50",
  archived: "bg-ink-muted/30 text-ink-muted ring-1 ring-ink-muted/40",
};

export function YearStatusBadge({ status }: { status: YearStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2.5 py-1 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] ${STATUS_TONE[status]}`}
    >
      {yearStatusLabel(status)}
    </span>
  );
}
