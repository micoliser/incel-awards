"use client";

import Link from "next/link";
import { BrandMark } from "@/components/brand-logos";
import { VotingCountdownBar } from "@/components/voting-countdown-bar";

type SiteHeaderProps = {
  year?: number;
  votingOpensAt?: string | null;
  votingClosesAt?: string | null;
  /** When true, skip the layout spacer so a full-bleed hero can sit under the bar. */
  overlay?: boolean;
};

export function SiteHeader({
  year,
  votingOpensAt = null,
  votingClosesAt = null,
  overlay = false,
}: SiteHeaderProps) {
  const hasSchedule = Boolean(votingOpensAt || votingClosesAt);
  const spacerClass = hasSchedule
    ? "h-[8.25rem] sm:h-[8.75rem]"
    : "h-[4.75rem] sm:h-[5.25rem]";

  return (
    <>
      <div className="fixed inset-x-0 top-0 z-50">
        <VotingCountdownBar
          year={year}
          votingOpensAt={votingOpensAt}
          votingClosesAt={votingClosesAt}
        />
        <header className="border-b border-[var(--rule)] bg-[color-mix(in_srgb,var(--ground)_78%,transparent)] backdrop-blur-xl">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-3 sm:px-8 sm:py-3.5">
            <Link
              href="/"
              className="flex items-center gap-3.5 font-[family-name:var(--font-display)] text-sm font-semibold tracking-tight text-ink sm:text-base"
            >
              <BrandMark size={44} className="h-10 w-auto shrink-0 sm:h-11" />
              <span className="leading-tight">
                Incel Group
                <span className="mt-0.5 block font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.18em] text-gold">
                  Employee Awards
                </span>
              </span>
            </Link>
            <nav
              aria-label="Primary"
              className="flex items-center gap-5 font-[family-name:var(--font-label)] text-[11px] font-medium uppercase tracking-[0.14em] text-ink-muted"
            >
              {year ? (
                <>
                  <Link className="thread-link hover:text-gold-bright" href={`/${year}`}>
                    {year}
                  </Link>
                  <Link
                    className="thread-link hover:text-gold-bright"
                    href={`/${year}/awards`}
                  >
                    Awards
                  </Link>
                  <Link
                    className="thread-link hover:text-gold-bright"
                    href={`/${year}/results`}
                  >
                    Results
                  </Link>
                </>
              ) : (
                <Link className="thread-link hover:text-gold-bright" href="/2026">
                  2026
                </Link>
              )}
            </nav>
          </div>
          <div className="h-0.5 weave-band opacity-90" aria-hidden />
        </header>
      </div>
      {overlay ? null : <div className={spacerClass} aria-hidden />}
    </>
  );
}
