import { percentLabel, votingModeLabel } from "@/lib/format";
import type { Award } from "@/lib/types";

export function VotingRulesPanel({ award }: { award: Award }) {
  return (
    <div className="stage-panel px-5 py-5">
      <h2 className="font-[family-name:var(--font-display)] text-base tracking-tight text-ink">
        How voting works
      </h2>
      <p className="mt-2 text-sm text-ink-muted">
        {votingModeLabel(award.voting_mode)}
      </p>
      {award.voting_mode === "weighted" ? (
        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              Executive share
            </dt>
            <dd className="mt-1 font-[family-name:var(--font-display)] text-2xl text-indigo">
              {percentLabel(award.executive_weight)}
            </dd>
          </div>
          <div>
            <dt className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              Staff share
            </dt>
            <dd className="mt-1 font-[family-name:var(--font-display)] text-2xl text-indigo">
              {percentLabel(award.staff_weight)}
            </dd>
          </div>
        </dl>
      ) : null}
      {award.voting_mode === "staff_shortlist" ? (
        <p className="mt-3 max-w-prose text-sm text-ink">
          All eligible staff (and executives voting as ordinary ballots) pick
          one nominee from the shortlist.
        </p>
      ) : null}
      {award.voting_mode === "staff_open" ? (
        <p className="mt-3 max-w-prose text-sm text-ink">
          Search the staff roster and choose any colleague. No scored criteria
          apply.
        </p>
      ) : null}
    </div>
  );
}
