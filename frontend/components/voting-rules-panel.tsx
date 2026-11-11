import { votingModeLabel } from "@/lib/format";
import type { Award } from "@/lib/types";

/** Public voting-mode copy only — share ratios are committee-only. */
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
        <p className="mt-3 max-w-prose text-sm text-ink">
          Eligible colleagues cast one pick per award. Executive and staff
          ballots are combined with committee weights when results are tallied.
        </p>
      ) : null}
      {award.voting_mode === "staff_shortlist" ? (
        <p className="mt-3 max-w-prose text-sm text-ink">
          All eligible staff (and executives voting as ordinary ballots) pick
          one nominee from the shortlist when voting opens.
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
