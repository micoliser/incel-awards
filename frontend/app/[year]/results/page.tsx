import Link from "next/link";
import { notFound } from "next/navigation";
import { DivisionLogo } from "@/components/brand-logos";
import { getAwards, getResults, getYear } from "@/lib/api";
import {
  divisionLabel,
  formatDateTime,
  scorePercentLabel,
  votingModeLabel,
} from "@/lib/format";
import type { AwardResult, Division, VotingMode } from "@/lib/types";

/** Results read params / preview searchParams; allow blocking navigation. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string }>;
  searchParams: Promise<{ preview?: string }>;
};

const PLANE: Record<Division, string> = {
  tourism: "bg-tourism",
  global: "bg-global",
  shared: "bg-shared",
};

export async function generateMetadata({ params }: PageProps) {
  const { year } = await params;
  return { title: `Results ${year}` };
}

export default async function ResultsPage({ params, searchParams }: PageProps) {
  const { year: yearParam } = await params;
  const { preview } = await searchParams;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  const fetch = await getResults(year, preview);

  if (fetch.state === "unpublished" || fetch.state === "unavailable") {
    const unpublished = fetch.state === "unpublished";
    return (
      <main className="mx-auto max-w-xl px-5 py-16 sm:px-8 sm:py-20">
        <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
          {yearMeta.title}
        </p>
        <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink">
          Results
        </h1>
        <p className="mt-6 text-base leading-relaxed text-ink-muted">
          {unpublished
            ? `Results for ${yearMeta.title} are not public yet. They stay private to the awards committee until after the ceremony. The public results page will open once the committee publishes.`
            : "Results could not be loaded right now. Refresh this page shortly, or check back once the season is published."}
        </p>
        {yearMeta.results_published_at ? (
          <p className="mt-3 text-sm text-ink-muted">
            Publish time on record: {formatDateTime(yearMeta.results_published_at)}
          </p>
        ) : null}
        {!unpublished ? (
          <p className="mt-6">
            <Link
              href={`/${year}/results`}
              className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ground hover:brightness-110"
            >
              Retry
            </Link>
          </p>
        ) : null}
        <BackLink year={year} />
      </main>
    );
  }

  const awardsCatalogue = await getAwards(year);
  const bySlug = new Map(awardsCatalogue.map((a) => [a.slug, a]));

  const enriched: AwardResult[] = fetch.data.awards.map((row) => {
    const meta = bySlug.get(row.award_slug);
    return {
      ...row,
      award_name: meta?.name ?? row.award_slug,
      division: meta?.division,
    };
  });

  const grouped = {
    tourism: enriched.filter((a) => a.division === "tourism"),
    global: enriched.filter((a) => a.division === "global"),
    shared: enriched.filter((a) => a.division === "shared" || !a.division),
  };

  return (
    <main className="mx-auto max-w-3xl px-5 py-14 sm:px-8 sm:py-16">
      <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
        {fetch.data.title}
      </p>
      <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink sm:text-4xl">
        Results
      </h1>
      {fetch.data.preview ? (
        <p className="mt-4 border border-[var(--gold)] bg-[color-mix(in_srgb,var(--gold)_18%,var(--surface))] px-4 py-3 text-sm text-ink">
          Committee preview only. These results are not public. Leave{" "}
          <span className="font-medium">results published at</span> empty in
          admin until after the award ceremony.
        </p>
      ) : (
        <p className="mt-4 max-w-prose text-sm text-ink-muted">
          Published {formatDateTime(fetch.data.results_published_at)}. Winners
          and tallies for the season.
        </p>
      )}

      {preview ? (
        <p className="mt-5">
          <Link
            href={`/${year}/results/audit?preview=${encodeURIComponent(preview)}`}
            className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ground hover:brightness-110"
          >
            Voting breakdown
          </Link>
          <span className="mt-2 block text-sm text-ink-muted">
            Simple scores and who voted for whom (committee only).
          </span>
        </p>
      ) : null}

      <div className="mt-12 space-y-14">
        <ResultsDivision
          title="Tourism awards"
          plane="bg-tourism"
          division="tourism"
          rows={grouped.tourism}
        />
        <ResultsDivision
          title="Global awards"
          plane="bg-global"
          division="global"
          rows={grouped.global}
        />
        <ResultsDivision
          title="General awards"
          plane="bg-shared"
          division="shared"
          rows={grouped.shared}
        />
      </div>

      <BackLink year={year} />
    </main>
  );
}

function ResultsDivision({
  title,
  plane,
  division,
  rows,
}: {
  title: string;
  plane: string;
  division: Division;
  rows: AwardResult[];
}) {
  if (!rows.length) return null;
  return (
    <section>
      <div className="mb-5 flex items-center gap-3">
        <span className={`h-7 w-1.5 ${plane}`} aria-hidden />
        <DivisionLogo
          division={division}
          size={52}
          className="h-12 w-auto shrink-0 sm:h-14"
        />
        <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink">
          {title}
        </h2>
      </div>
      <div className="axial-rule mb-6" />
      <ul className="space-y-5">
        {rows.map((row) => (
          <ResultCard key={row.award_slug} row={row} />
        ))}
      </ul>
    </section>
  );
}

function ResultCard({ row }: { row: AwardResult }) {
  const division = row.division;
  const winners = row.winners;
  const tied = winners.length > 1 || winners.some((w) => w.is_tie);
  const winnerLabel = tied
    ? winners.map((w) => w.display_name).join(" · ")
    : (winners[0]?.display_name ?? "Pending");

  const showShares =
    row.voting_mode === "weighted" && row.nominees.some((n) => n.is_winner);

  return (
    <li className="stage-panel overflow-hidden">
      {division ? (
        <span className={`block h-1.5 w-full ${PLANE[division]}`} aria-hidden />
      ) : (
        <span className="block h-1.5 w-full bg-indigo" aria-hidden />
      )}
      <div className="px-5 py-5">
        <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted">
          {division ? `${divisionLabel(division)} · ` : ""}
          {votingModeLabel(row.voting_mode as VotingMode)}
        </p>
        <h3 className="mt-2 font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
          {row.award_name ?? row.award_slug}
        </h3>
        <p className="mt-3 text-sm text-ink-muted">
          {tied ? "Tie (committee review)" : "Winner"}
        </p>
        <p className="mt-1 font-[family-name:var(--font-display)] text-2xl tracking-tight text-indigo">
          {winnerLabel}
        </p>

        {showShares ? (
          <ul className="mt-5 space-y-2 border-t border-[var(--rule)] pt-4">
            {row.nominees.slice(0, 5).map((n) => (
              <li
                key={`${n.nominee_id ?? n.selected_person_id}-${n.display_name}`}
                className="flex items-baseline justify-between gap-4 text-sm"
              >
                <span className={n.is_winner ? "font-medium text-ink" : "text-ink-muted"}>
                  {n.display_name}
                </span>
                <span className="font-[family-name:var(--font-label)] text-xs font-semibold tabular-nums tracking-wide text-indigo">
                  {scorePercentLabel(n.score)}
                </span>
              </li>
            ))}
          </ul>
        ) : row.voting_mode !== "weighted" && row.nominees.length > 0 ? (
          <ul className="mt-5 space-y-2 border-t border-[var(--rule)] pt-4">
            {row.nominees.slice(0, 5).map((n) => (
              <li
                key={`${n.nominee_id ?? n.selected_person_id}-${n.display_name}`}
                className="flex items-baseline justify-between gap-4 text-sm"
              >
                <span className={n.is_winner ? "font-medium text-ink" : "text-ink-muted"}>
                  {n.display_name}
                </span>
                <span className="font-[family-name:var(--font-label)] text-xs font-semibold tabular-nums tracking-wide text-indigo">
                  {n.total_votes} vote{n.total_votes === 1 ? "" : "s"}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </li>
  );
}

function BackLink({ year }: { year: number }) {
  return (
    <p className="mt-12">
      <Link
        href={`/${year}`}
        className="thread-link font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-indigo"
      >
        Back to {year} hub
      </Link>
    </p>
  );
}
