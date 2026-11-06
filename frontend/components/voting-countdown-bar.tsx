"use client";

import { useSyncExternalStore } from "react";

type CountdownMode = "opens" | "closes" | null;

type VotingCountdownBarProps = {
  year?: number;
  votingOpensAt?: string | null;
  votingClosesAt?: string | null;
};

type Parts = {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
};

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function splitRemaining(ms: number): Parts {
  const total = Math.max(0, Math.floor(ms / 1000));
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  return { days, hours, minutes, seconds };
}

function resolveMode(
  now: number,
  opensAt: string | null | undefined,
  closesAt: string | null | undefined,
): { mode: CountdownMode; target: number | null } {
  const opens = opensAt ? Date.parse(opensAt) : NaN;
  const closes = closesAt ? Date.parse(closesAt) : NaN;

  if (Number.isFinite(opens) && now < opens) {
    return { mode: "opens", target: opens };
  }
  if (Number.isFinite(closes) && now < closes) {
    if (!Number.isFinite(opens) || now >= opens) {
      return { mode: "closes", target: closes };
    }
  }
  return { mode: null, target: null };
}

function Unit({ value, label }: { value: string; label: string }) {
  return (
    <span className="inline-flex min-w-[2.75rem] flex-col items-center sm:min-w-[3.25rem]">
      <span className="font-[family-name:var(--font-display)] text-lg font-semibold leading-none tracking-tight tabular-nums sm:text-2xl">
        {value}
      </span>
      <span className="mt-0.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.16em] opacity-80 sm:text-[11px]">
        {label}
      </span>
    </span>
  );
}

let clientNow = 0;

function subscribeNow(onStoreChange: () => void) {
  clientNow = Date.now();
  onStoreChange();
  const id = window.setInterval(() => {
    clientNow = Date.now();
    onStoreChange();
  }, 1000);
  return () => window.clearInterval(id);
}

function getNowSnapshot() {
  return clientNow;
}

function getServerNowSnapshot() {
  return 0;
}

export function VotingCountdownBar({
  year,
  votingOpensAt,
  votingClosesAt,
}: VotingCountdownBarProps) {
  const now = useSyncExternalStore(
    subscribeNow,
    getNowSnapshot,
    getServerNowSnapshot,
  );

  if (now === 0) {
    // Reserve space when a schedule exists so the fixed header does not jump.
    if (!votingOpensAt && !votingClosesAt) return null;
    return (
      <div
        className="border-b border-black/30 bg-indigo text-ink"
        aria-hidden
      >
        <div className="mx-auto h-[3.25rem] max-w-6xl sm:h-[3.5rem]" />
      </div>
    );
  }

  const { mode, target } = resolveMode(now, votingOpensAt, votingClosesAt);
  if (!mode || target == null) return null;

  const parts = splitRemaining(target - now);
  const label =
    mode === "opens"
      ? `Voting opens in${year ? ` · ${year}` : ""}`
      : `Voting closes in${year ? ` · ${year}` : ""}`;
  const tone =
    mode === "opens"
      ? "bg-indigo text-ink"
      : "bg-gradient-to-r from-gold to-gold-bright text-ground";

  return (
    <div
      role="status"
      aria-live="polite"
      className={`border-b border-black/30 ${tone}`}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-5 gap-y-2 px-4 py-2.5 sm:justify-between sm:px-8 sm:py-3">
        <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.2em] sm:text-xs">
          {label}
        </p>
        <div className="flex items-end gap-2 sm:gap-3">
          {parts.days > 0 ? (
            <>
              <Unit
                value={String(parts.days)}
                label={parts.days === 1 ? "Day" : "Days"}
              />
              <span className="pb-3 text-lg opacity-50 sm:text-2xl" aria-hidden>
                :
              </span>
            </>
          ) : null}
          <Unit value={pad(parts.hours)} label="Hrs" />
          <span className="pb-3 text-lg opacity-50 sm:text-2xl" aria-hidden>
            :
          </span>
          <Unit value={pad(parts.minutes)} label="Min" />
          <span className="pb-3 text-lg opacity-50 sm:text-2xl" aria-hidden>
            :
          </span>
          <Unit value={pad(parts.seconds)} label="Sec" />
        </div>
      </div>
    </div>
  );
}
