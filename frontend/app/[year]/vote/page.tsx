import { notFound } from "next/navigation";
import { BallotShell } from "@/components/vote/ballot-shell";
import { getYear } from "@/lib/api";

/** Ballot reads searchParams token; not an instant shell. */
export const instant = false;

type PageProps = {
  params: Promise<{ year: string }>;
  searchParams: Promise<{ token?: string }>;
};

export async function generateMetadata({ params }: PageProps) {
  const { year } = await params;
  // Never put ?token= into title/description/OG; ballot links are personal.
  return {
    title: `Vote ${year}`,
    robots: { index: false, follow: false },
    referrer: "no-referrer",
  };
}

export default async function VotePage({ params, searchParams }: PageProps) {
  const { year: yearParam } = await params;
  const { token } = await searchParams;
  const year = Number(yearParam);
  const yearMeta = await getYear(year);
  if (!yearMeta) notFound();

  return (
    <BallotShell
      year={year}
      yearTitle={yearMeta.title}
      initialToken={token?.trim() || null}
    />
  );
}
