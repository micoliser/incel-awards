"use client";

import { NomineeRadioGroup } from "@/components/vote/nominee-radio-group";
import { PersonSearchPicker } from "@/components/vote/person-search-picker";
import { divisionLabel, votingModeLabel } from "@/lib/format";
import type { BallotAward, Division } from "@/lib/types";

const PLANE: Record<Division, string> = {
  tourism: "bg-tourism",
  global: "bg-global",
  shared: "bg-shared",
};

export type VoteSelection =
  | { kind: "nominee"; nominee_id: number }
  | { kind: "person"; selected_person_id: number; display_name: string }
  | null;

type AwardVoteSectionProps = {
  year: number;
  token: string;
  award: BallotAward;
  selection: VoteSelection;
  onChange: (selection: VoteSelection) => void;
  disabled?: boolean;
  showError?: boolean;
};

export function AwardVoteSection({
  year,
  token,
  award,
  selection,
  onChange,
  disabled = false,
  showError = false,
}: AwardVoteSectionProps) {
  const unanswered = showError && selection == null;

  const emptyShortlist =
    award.voting_mode !== "staff_open" && award.nominees.length === 0;

  return (
    <section
      id={`award-${award.slug}`}
      tabIndex={-1}
      className={`scroll-mt-24 border bg-surface outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 ${
        unanswered ? "border-[var(--danger)]" : "border-[var(--rule)]"
      }`}
      data-invalid={unanswered || undefined}
      aria-labelledby={`award-${award.slug}-title`}
    >
      <span className={`block h-1.5 w-full ${PLANE[award.division]}`} aria-hidden />
      <div className="px-4 py-5 sm:px-5">
        <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted">
          {divisionLabel(award.division)} · {votingModeLabel(award.voting_mode)}
        </p>
        <h3
          id={`award-${award.slug}-title`}
          className="mt-2 font-[family-name:var(--font-display)] text-xl tracking-tight text-ink"
        >
          {award.name}
        </h3>
        {award.description ? (
          <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-muted">
            {award.description}
          </p>
        ) : null}

        <div className="mt-5">
          {award.voting_mode === "staff_open" ? (
            <PersonSearchPicker
              year={year}
              token={token}
              awardName={award.name}
              disabled={disabled}
              value={
                selection?.kind === "person"
                  ? {
                      id: selection.selected_person_id,
                      display_name: selection.display_name,
                    }
                  : null
              }
              onChange={(person) =>
                onChange(
                  person
                    ? {
                        kind: "person",
                        selected_person_id: person.id,
                        display_name: person.display_name,
                      }
                    : null,
                )
              }
            />
          ) : emptyShortlist ? (
            <p className="text-sm text-ink-muted">
              No confirmed nominees are listed for this award yet. Check back
              once the committee confirms the shortlist.
            </p>
          ) : (
            <NomineeRadioGroup
              awardSlug={award.slug}
              awardName={award.name}
              nominees={award.nominees}
              disabled={disabled}
              value={selection?.kind === "nominee" ? selection.nominee_id : null}
              onChange={(nomineeId) =>
                onChange({ kind: "nominee", nominee_id: nomineeId })
              }
            />
          )}
        </div>

        {unanswered && !emptyShortlist ? (
          <p
            id={`award-${award.slug}-error`}
            className="mt-3 text-sm text-[var(--danger)]"
            role="alert"
          >
            Choose a selection for this award.
          </p>
        ) : null}
      </div>
    </section>
  );
}
