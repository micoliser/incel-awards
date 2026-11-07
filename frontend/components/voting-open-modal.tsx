"use client";

import { useEffect, useId, useState } from "react";
import { formatDateTime } from "@/lib/format";

type VotingOpenModalProps = {
  year: number;
  status?: string | null;
  votingOpensAt?: string | null;
  votingClosesAt?: string | null;
};

function isVotingOpenNow(
  status: string | null | undefined,
  opensAt: string | null | undefined,
  closesAt: string | null | undefined,
  nowMs: number,
): boolean {
  if (status === "voting") return true;
  const opens = opensAt ? Date.parse(opensAt) : NaN;
  const closes = closesAt ? Date.parse(closesAt) : NaN;
  if (!Number.isFinite(opens)) return false;
  if (nowMs < opens) return false;
  if (Number.isFinite(closes) && nowMs >= closes) return false;
  return true;
}

export function VotingOpenModal({
  year,
  status = null,
  votingOpensAt = null,
  votingClosesAt = null,
}: VotingOpenModalProps) {
  const titleId = useId();
  const descId = useId();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Show on every mount/refresh while the window is open (no persistence).
    const shouldShow = isVotingOpenNow(
      status,
      votingOpensAt,
      votingClosesAt,
      Date.now(),
    );
    queueMicrotask(() => setOpen(shouldShow));
  }, [status, votingOpensAt, votingClosesAt]);

  useEffect(() => {
    if (!open) return;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center px-5"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/70"
        aria-label="Dismiss voting notice"
        onClick={() => setOpen(false)}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative z-[1] w-full max-w-md border border-[var(--rule)] bg-surface px-6 py-6 shadow-[0_24px_48px_-28px_rgba(0,0,0,0.85)]"
      >
        <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.18em] text-gold">
          {year} season
        </p>
        <h2
          id={titleId}
          className="mt-2 font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink"
        >
          Voting is open
        </h2>
        <p id={descId} className="mt-3 text-sm leading-relaxed text-ink-muted">
          Use the personal ballot link from your email to cast your votes.
          {votingClosesAt ? (
            <>
              {" "}
              Voting closes {formatDateTime(votingClosesAt)}.
            </>
          ) : null}
        </p>
        <div className="mt-6">
          <button
            type="button"
            autoFocus
            onClick={() => setOpen(false)}
            className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ground transition-[filter] hover:brightness-110"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
