import Image from "next/image";
import Link from "next/link";
import { divisionLabel, votingModeLabel } from "@/lib/format";
import type { Award, Division } from "@/lib/types";

const DIVISION_PLANE: Record<Division, string> = {
  tourism: "bg-tourism",
  global: "bg-global",
  shared: "bg-shared",
};

type AwardCardProps = {
  year: number;
  award: Award;
};

function excerpt(text: string, max = 140): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max).replace(/\s+\S*$/, "")}…`;
}

export function AwardCard({ year, award }: AwardCardProps) {
  const nominees = award.nominees ?? [];
  const confirmed = nominees.filter((n) => n.is_confirmed !== false).length;

  let meta: string;
  if (award.voting_mode === "staff_open") {
    meta = "Open roster choice";
  } else if (confirmed > 0) {
    meta = `${confirmed} nominee${confirmed === 1 ? "" : "s"}`;
  } else {
    meta = "View criteria and nominees";
  }

  return (
    <Link
      href={`/${year}/awards/${award.slug}`}
      className="group stage-panel block overflow-hidden transition-[transform,border-color] duration-400 ease-[var(--ease-out-expo)] hover:-translate-y-1 hover:border-gold/50"
    >
      <span
        className={`block h-1 w-full ${DIVISION_PLANE[award.division]}`}
        aria-hidden
      />
      <div className="px-5 py-5">
        <div className="flex items-start justify-between gap-3">
          <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted">
            {divisionLabel(award.division)} · {votingModeLabel(award.voting_mode)}
          </p>
          <Image
            src="/images/award-trophy.png"
            alt=""
            width={40}
            height={40}
            className="h-10 w-10 shrink-0 object-contain transition-transform duration-500 ease-[var(--ease-out-expo)] group-hover:scale-110 group-hover:-rotate-6"
          />
        </div>
        <h3 className="mt-2 font-[family-name:var(--font-display)] text-lg leading-snug tracking-tight text-ink transition-colors duration-300 group-hover:text-gold-bright">
          {award.name}
        </h3>
        {award.description ? (
          <p className="mt-3 text-sm leading-relaxed text-ink-muted">
            {excerpt(award.description)}
          </p>
        ) : null}
        <p className="mt-4 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-gold">
          {meta}
        </p>
      </div>
    </Link>
  );
}
