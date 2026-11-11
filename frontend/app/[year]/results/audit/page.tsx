import Link from "next/link";
import { notFound } from "next/navigation";
import { getResultsAudit, getYear } from "@/lib/api";
import {
  companyLabel,
  divisionLabel,
  formatDateTime,
  scorePercentLabel,
  votingModeLabel,
} from "@/lib/format";
import type { AuditAward, AuditNomineeRow, Division } from "@/lib/types";

/** Audit reads params / preview searchParams; allow blocking navigation. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string }>;
  searchParams: Promise<{ preview?: string }>;
};

export async function generateMetadata({ params }: PageProps) {
  const { year } = await params;
  return {
    title: `Voting breakdown ${year}`,
    robots: { index: false, follow: false },
  };
}

function pctPoints(fraction: number | string | null | undefined): number {
  const n = typeof fraction === "number" ? fraction : Number(fraction);
  if (!Number.isFinite(n)) return 0;
  return Math.round(n * 1000) / 10;
}

export default async function ResultsAuditPage({
  params,
  searchParams,
}: PageProps) {
  const { year: yearParam } = await params;
  const { preview } = await searchParams;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  const fetch = await getResultsAudit(year, preview);

  if (fetch.state !== "ready") {
    return (
      <main className="mx-auto max-w-xl px-5 py-16 sm:px-8 sm:py-20">
        <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink">
          Voting breakdown
        </h1>
        <p className="mt-6 text-base leading-relaxed text-ink-muted">
          {fetch.state === "forbidden"
            ? "This page is for the awards committee only. Open it from the private results link."
            : "Could not load this page right now. Try again shortly."}
        </p>
        <p className="mt-8">
          <Link
            href={`/${year}/results`}
            className="thread-link font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-indigo"
          >
            Back to results
          </Link>
        </p>
      </main>
    );
  }

  const report = fetch.data;
  const s = report.summary;
  const previewQs = preview ? `?preview=${encodeURIComponent(preview)}` : "";
  const participation = `${Math.round(Number(s.participation_rate) * 1000) / 10}%`;

  return (
    <main className="mx-auto max-w-3xl px-5 py-14 sm:px-8 sm:py-16">
      <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
        {report.title}
      </p>
      <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink sm:text-4xl">
        Voting breakdown
      </h1>
      <p className="mt-4 border border-[var(--gold)] bg-[color-mix(in_srgb,var(--gold)_18%,var(--surface))] px-4 py-3 text-sm text-ink">
        Committee only — do not share this link publicly.
      </p>

      <section className="mt-10">
        <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
          At a glance
        </h2>
        <ul className="mt-4 space-y-2 text-base text-ink-muted">
          <li>
            <span className="text-ink">{s.unique_voters}</span> people voted out of{" "}
            <span className="text-ink">{s.ballots_active}</span> ballots sent (
            {participation})
          </li>
          <li>
            <span className="text-ink">{s.total_votes_cast}</span> votes cast across{" "}
            <span className="text-ink">{s.awards_count}</span> awards
          </li>
          <li>Voting closed {formatDateTime(report.voting_closes_at)}</li>
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
          How winners were decided
        </h2>
        <div className="mt-4 space-y-4 text-base leading-relaxed text-ink-muted">
          <p>
            <span className="font-medium text-ink">Most awards:</span> one person,
            one vote. Highest count wins.
          </p>
          <p>
            <span className="font-medium text-ink">
              Employee, Supervisor, and Department awards:
            </span>{" "}
            Executive management and staff scores are added together. Each award
            has a fixed split (for example 30% Executive management and 70%
            staff). The Executive management share is split evenly across the
            Executive management voters for that award. The staff share is split
            by how many staff voted for each option.
          </p>
        </div>
      </section>

      <div className="mt-12 space-y-10">
        {report.awards.map((award) => (
          <AwardBreakdown key={award.award_slug} award={award} />
        ))}
      </div>

      <p className="mt-14">
        <Link
          href={`/${year}/results${previewQs}`}
          className="thread-link font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-indigo"
        >
          Back to results
        </Link>
      </p>
    </main>
  );
}

function AwardBreakdown({ award }: { award: AuditAward }) {
  const winnerNames = award.winners.map((w) => w.display_name).join(" and ");
  const tied = award.winners.length > 1 || award.winners.some((w) => w.is_tie);
  const isWeighted = award.voting_mode === "weighted";
  const calc = award.calculation as {
    executive_weight?: string;
    staff_weight?: string;
    eligible_exec_count?: number;
    exec_vote_value?: string;
    total_exec_votes_cast?: number;
    total_staff_votes_cast?: number;
  };

  const execPct = pctPoints(calc.executive_weight);
  const staffPct = pctPoints(calc.staff_weight);
  const eCount = calc.eligible_exec_count ?? 0;
  const perExecPct = pctPoints(calc.exec_vote_value);
  const staffVotesCast = calc.total_staff_votes_cast ?? 0;

  return (
    <section className="stage-panel px-5 py-6">
      <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted">
        {divisionLabel(award.division as Division)} ·{" "}
        {isWeighted
          ? "Executive management + staff"
          : votingModeLabel(award.voting_mode)}
      </p>
      <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
        {award.award_name}
      </h2>

      {award.winners.length ? (
        <p className="mt-3 text-base text-ink">
          {tied ? "Tie" : "Winner"}:{" "}
          <span className="font-medium text-indigo">{winnerNames}</span>
        </p>
      ) : (
        <p className="mt-3 text-base text-ink-muted">No votes yet</p>
      )}

      {isWeighted ? (
        <WeightedWorkedExample
          execPct={execPct}
          staffPct={staffPct}
          eCount={eCount}
          perExecPct={perExecPct}
          staffVotesCast={staffVotesCast}
          nominees={award.nominees}
        />
      ) : (
        <>
          <p className="mt-2 text-sm text-ink-muted">
            {award.votes_cast} vote{award.votes_cast === 1 ? "" : "s"}
          </p>
          {award.nominees.length > 0 ? (
            <ul className="mt-5 space-y-2 border-t border-[var(--rule)] pt-4">
              {award.nominees.map((n) => (
                <li
                  key={`${n.nominee_id ?? n.selected_person_id}-${n.display_name}`}
                  className="flex items-baseline justify-between gap-4 text-sm"
                >
                  <span
                    className={
                      n.is_winner ? "font-medium text-ink" : "text-ink-muted"
                    }
                  >
                    {n.display_name}
                    {n.is_winner ? (n.is_tie ? " (tie)" : " (winner)") : ""}
                  </span>
                  <span className="tabular-nums text-ink">
                    {n.total_votes} vote{n.total_votes === 1 ? "" : "s"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      )}

      {award.ballots.length > 0 ? (
        <details className="mt-5 border-t border-[var(--rule)] pt-4">
          <summary className="cursor-pointer font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-indigo">
            Who voted ({award.ballots.length})
          </summary>
          <ul className="mt-4 space-y-3">
            {award.ballots.map((b) => (
              <li
                key={`${b.voter_id}-${b.choice_name}-${b.updated_at}`}
                className="text-sm leading-snug"
              >
                <span className="font-medium text-ink">{b.voter_name}</span>
                <span className="text-ink-muted">
                  {" "}
                  ({companyLabel(b.voter_company)}
                  {b.electorate_at_vote === "executive"
                    ? " · Executive management"
                    : ""}
                  )
                </span>
                <span className="text-ink-muted"> voted for </span>
                <span className="text-ink">{b.choice_name}</span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

function WeightedWorkedExample({
  execPct,
  staffPct,
  eCount,
  perExecPct,
  staffVotesCast,
  nominees,
}: {
  execPct: number;
  staffPct: number;
  eCount: number;
  perExecPct: number;
  staffVotesCast: number;
  nominees: AuditNomineeRow[];
}) {
  return (
    <div className="mt-5 space-y-5 border-t border-[var(--rule)] pt-4">
      <div className="text-sm leading-relaxed text-ink-muted">
        <p className="font-medium text-ink">
          Score split: {execPct}% Executive management · {staffPct}% staff
        </p>
        <p className="mt-2">
          There {eCount === 1 ? "is" : "are"} {eCount} Executive management
          voter{eCount === 1 ? "" : "s"} for this award, so each of their votes
          is worth {perExecPct}%
          {eCount > 0 ? ` (${execPct}% ÷ ${eCount})` : ""}.
        </p>
        <p className="mt-2">
          Staff share the remaining {staffPct}% according to how many of the{" "}
          {staffVotesCast} staff vote{staffVotesCast === 1 ? "" : "s"} each
          option received.
        </p>
      </div>

      <ul className="space-y-4">
        {nominees.map((n) => {
          const execShare = pctPoints(n.exec_share);
          const staffShare = pctPoints(n.staff_share);
          const total = pctPoints(n.score);
          const staffLine =
            staffVotesCast > 0
              ? `${n.staff_votes} of ${staffVotesCast} staff votes × ${staffPct}% = ${staffShare}%`
              : `No staff votes cast = 0%`;

          return (
            <li
              key={`${n.nominee_id ?? n.selected_person_id}-${n.display_name}`}
              className="rounded-sm bg-ground-deep/40 px-4 py-3 text-sm"
            >
              <p
                className={
                  n.is_winner
                    ? "font-medium text-indigo"
                    : "font-medium text-ink"
                }
              >
                {n.display_name}
                {n.is_winner ? (n.is_tie ? " (tie)" : " (winner)") : ""}
                <span className="ml-2 tabular-nums text-ink">
                  {scorePercentLabel(n.score)}
                </span>
              </p>
              <ul className="mt-2 space-y-1 text-ink-muted">
                <li>
                  Executive management: {n.exec_votes} vote
                  {n.exec_votes === 1 ? "" : "s"} × {perExecPct}% = {execShare}%
                </li>
                <li>Staff: {staffLine}</li>
                <li className="text-ink">
                  Total: {execShare}% + {staffShare}% = {total}%
                </li>
              </ul>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
