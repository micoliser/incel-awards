import Link from "next/link";
import { notFound } from "next/navigation";
import { AwardCard } from "@/components/award-card";
import { ConfettiSplash } from "@/components/confetti-splash";
import { getAwards, getYear } from "@/lib/api";
import { divisionLabel } from "@/lib/format";
import type { Division } from "@/lib/types";

/** Catalogue filter uses searchParams. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string }>;
  searchParams: Promise<{ division?: string }>;
};

const FILTERS: Array<"all" | Division> = ["all", "tourism", "global", "shared"];

export async function generateMetadata({ params }: PageProps) {
  const { year } = await params;
  return { title: `Awards ${year}` };
}

export default async function AwardsCataloguePage({
  params,
  searchParams,
}: PageProps) {
  const { year: yearParam } = await params;
  const { division: divisionParam } = await searchParams;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  const awards = (await getAwards(year))
    .filter((a) => a.is_active !== false)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

  const activeFilter =
    divisionParam && FILTERS.includes(divisionParam as Division)
      ? (divisionParam as Division)
      : "all";

  const filtered =
    activeFilter === "all"
      ? awards
      : awards.filter((a) => a.division === activeFilter);

  return (
    <main className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
      <ConfettiSplash />
      <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
        <Link href={`/${year}`} className="thread-link">
          {yearMeta.title}
        </Link>
      </p>
      <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink sm:text-4xl">
        Award catalogue
      </h1>
      <p className="mt-3 max-w-prose text-sm text-ink-muted">
        Filter by division. Open an award for about, criteria, and how voting
        works.
      </p>

      <div
        className="mt-8 flex flex-wrap gap-2"
        role="group"
        aria-label="Filter by division"
      >
        {FILTERS.map((f) => {
          const href =
            f === "all" ? `/${year}/awards` : `/${year}/awards?division=${f}`;
          const selected = activeFilter === f;
          return (
            <Link
              key={f}
              href={href}
              className={`px-3 py-2 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors ${
                selected
                  ? "bg-gold text-ground"
                  : "bg-ground-deep text-ink-muted hover:text-ink"
              }`}
              aria-current={selected ? "true" : undefined}
            >
              {f === "all" ? "All" : divisionLabel(f)}
            </Link>
          );
        })}
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((award) => (
          <AwardCard key={award.slug} year={year} award={award} />
        ))}
      </div>
      {!filtered.length ? (
        <p className="mt-10 text-sm text-ink-muted">No awards in this filter.</p>
      ) : null}
    </main>
  );
}
