import Link from "next/link";
import { notFound } from "next/navigation";
import { AwardCard } from "@/components/award-card";
import { DivisionLogo } from "@/components/brand-logos";
import { ConfettiSplash } from "@/components/confetti-splash";
import { YearStatusBadge } from "@/components/year-status-badge";
import { getAwards, getYear } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Award, Division } from "@/lib/types";

/** Year hub reads route params + year meta; allow blocking navigation. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string }>;
};

function byDivision(awards: Award[], division: Division) {
  return awards
    .filter((a) => a.division === division && a.is_active !== false)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
}

export async function generateMetadata({ params }: PageProps) {
  const { year } = await params;
  const meta = await getYear(Number(year));
  return {
    title: meta?.title ?? `Awards ${year}`,
  };
}

export default async function YearHubPage({ params }: PageProps) {
  const { year: yearParam } = await params;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  const awards = await getAwards(year);
  const tourism = byDivision(awards, "tourism");
  const global = byDivision(awards, "global");
  const shared = byDivision(awards, "shared");

  return (
    <main>
      <ConfettiSplash />
      <section className="border-b border-[var(--rule)]">
        <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
          <div className="flex flex-wrap items-center gap-3">
            <YearStatusBadge status={yearMeta.status} />
            <span className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
              Opens {formatDateTime(yearMeta.voting_opens_at)} · Closes{" "}
              {formatDateTime(yearMeta.voting_closes_at)}
            </span>
          </div>
          <h1 className="animate-weft mt-6 max-w-3xl font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink sm:text-5xl">
            <span className="gold-shimmer">{yearMeta.title}</span>
          </h1>
          <p className="mt-5 max-w-prose text-base leading-relaxed text-ink-muted">
            {yearMeta.description}
          </p>
          <p className="mt-4 max-w-prose text-sm leading-relaxed text-ink">
            Tourism colleagues vote on Tourism categories; Global colleagues on
            Global. General categories are open to everyone. Have a ballot link?
            Open it from your email. There is no public vote entry without a
            personal token.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href={`/${year}/awards`}
              className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-3 font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-ground transition-[filter] duration-300 hover:brightness-110"
            >
              Browse all awards
            </Link>
            <Link
              href={`/${year}/vote`}
              className="thread-link inline-flex py-3 font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-gold"
            >
              Ballot info
            </Link>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-16 px-5 py-16 sm:px-8">
        <DivisionSection
          year={year}
          title="Tourism awards"
          plane="bg-tourism"
          division="tourism"
          awards={tourism}
        />
        <DivisionSection
          year={year}
          title="Global awards"
          plane="bg-global"
          division="global"
          awards={global}
        />
        <DivisionSection
          year={year}
          title="General awards"
          plane="bg-shared"
          division="shared"
          awards={shared}
        />
      </div>
    </main>
  );
}

function DivisionSection({
  year,
  title,
  plane,
  division,
  awards,
}: {
  year: number;
  title: string;
  plane: string;
  division: Division;
  awards: Award[];
}) {
  if (!awards.length) return null;
  return (
    <section className="animate-weft">
      <div className="mb-6 flex items-center gap-4">
        <span className={`h-8 w-2 ${plane}`} aria-hidden />
        <DivisionLogo
          division={division}
          size={52}
          className="h-12 w-auto shrink-0 sm:h-14"
        />
        <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink">
          {title}
        </h2>
      </div>
      <div className="axial-rule mb-8" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {awards.map((award) => (
          <AwardCard key={award.slug} year={year} award={award} />
        ))}
      </div>
    </section>
  );
}
