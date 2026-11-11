import Link from "next/link";
import { notFound } from "next/navigation";
import { AwardStageBanner } from "@/components/award-stage-banner";
import { DivisionLogo } from "@/components/brand-logos";
import { CriteriaList } from "@/components/criteria-list";
import { IdealWinnerList } from "@/components/ideal-winner-list";
import { VotingRulesPanel } from "@/components/voting-rules-panel";
import { YearStatusBadge } from "@/components/year-status-badge";
import { getAward, getYear } from "@/lib/api";
import { divisionLabel } from "@/lib/format";
import { idealWinnerLines } from "@/lib/ideal-winner";

/** Award detail reads route params + API data; allow blocking navigation. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string; slug: string }>;
};

export async function generateMetadata({ params }: PageProps) {
  const { year, slug } = await params;
  const award = await getAward(Number(year), slug);
  return { title: award?.name ?? slug };
}

export default async function AwardDetailPage({ params }: PageProps) {
  const { year: yearParam, slug } = await params;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  const award = await getAward(year, slug);
  if (!yearMeta || !award) notFound();

  return (
    <main className="mx-auto max-w-3xl px-5 py-14 sm:px-8">
      <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
        <Link href={`/${year}/awards`} className="thread-link">
          Awards
        </Link>
        <span aria-hidden> · </span>
        {divisionLabel(award.division)}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <DivisionLogo
          division={award.division}
          size={52}
          className="h-12 w-auto shrink-0 sm:h-14"
        />
        <YearStatusBadge status={yearMeta.status} />
      </div>
      <AwardStageBanner title={award.name} division={award.division} />

      <div className="mt-10 space-y-12">
        {award.description ? (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
              About the award
            </h2>
            <p className="mt-3 max-w-prose text-base leading-relaxed text-ink-muted">
              {award.description}
            </p>
          </section>
        ) : null}

        {idealWinnerLines(award.ideal_winner).length > 0 ? (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
              An ideal winner
            </h2>
            <div className="mt-3 max-w-prose">
              <IdealWinnerList text={award.ideal_winner} />
            </div>
          </section>
        ) : null}

        <VotingRulesPanel />

        {(award.criteria?.length ?? 0) > 0 ? (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
              Criteria
            </h2>
            <p className="mt-2 text-sm text-ink-muted">
              Guidance for voters: you pick a nominee; you do not score each
              criterion separately.
            </p>
            <div className="mt-6">
              <CriteriaList criteria={award.criteria ?? []} />
            </div>
          </section>
        ) : null}

        <section>
          <h2 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
            Shortlist
          </h2>
          <p className="mt-3 max-w-prose text-sm text-ink-muted">
            {award.voting_mode === "staff_open"
              ? "Open award: choose any eligible colleague on your personal ballot when voting opens."
              : "Nominees are not listed publicly. Eligible voters see the shortlist on their personal ballot when voting opens."}
          </p>
        </section>

        <p className="border-t border-[var(--rule)] pt-6 text-sm text-ink-muted">
          Season status: voting{" "}
          {yearMeta.status === "voting"
            ? "is open"
            : yearMeta.status === "closed" || yearMeta.status === "archived"
              ? "has closed"
              : "has not started"}
          . Ballots are issued by personal email link.
        </p>
      </div>
    </main>
  );
}
