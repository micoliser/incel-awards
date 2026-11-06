import { notFound } from "next/navigation";
import { SiteHeader } from "@/components/site-header";
import { getYear, listYears } from "@/lib/api";

/** Year chrome depends on route params + year meta; allow blocking navigation. */
export const instant = false;

type YearLayoutProps = {
  children: React.ReactNode;
  params: Promise<{ year: string }>;
};

export async function generateStaticParams() {
  const years = await listYears();
  return years.map((y) => ({ year: String(y.year) }));
}

export default async function YearLayout({ children, params }: YearLayoutProps) {
  const { year: yearParam } = await params;
  const year = Number(yearParam);
  if (!Number.isFinite(year) || year < 2000) notFound();

  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  return (
    <>
      <SiteHeader
        year={year}
        votingOpensAt={yearMeta.voting_opens_at}
        votingClosesAt={yearMeta.voting_closes_at}
      />
      <div className="flex-1">{children}</div>
    </>
  );
}
