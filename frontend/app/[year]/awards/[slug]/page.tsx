import Link from "next/link";
import { notFound } from "next/navigation";
import { AwardStageBanner } from "@/components/award-stage-banner";
import { DivisionLogo } from "@/components/brand-logos";
import { CriteriaList } from "@/components/criteria-list";
import { NomineeList } from "@/components/nominee-list";
import { VotingRulesPanel } from "@/components/voting-rules-panel";
import { YearStatusBadge } from "@/components/year-status-badge";
import { getAward, getYear } from "@/lib/api";
import { divisionLabel } from "@/lib/format";

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
      <p className="mt-6 max-w-prose text-base leading-relaxed text-ink-muted">
        {award.description}
      </p>

      <div className="mt-10 space-y-12">
        <VotingRulesPanel award={award} />

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
            Nominees
          </h2>
          <div className="mt-4">
            {award.voting_mode === "staff_open" ? (
              <p className="text-sm text-ink-muted">
                Open award: choose any eligible colleague on your ballot when
                voting opens.
              </p>
            ) : (
              <NomineeList nominees={award.nominees ?? []} />
            )}
          </div>
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
