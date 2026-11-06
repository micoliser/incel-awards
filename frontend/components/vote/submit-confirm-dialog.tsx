"use client";

import { useEffect, useId, useRef } from "react";

type SubmitConfirmDialogProps = {
  open: boolean;
  submitting: boolean;
  awardCount: number;
  onCancel: () => void;
  onConfirm: () => void;
};

export function SubmitConfirmDialog({
  open,
  submitting,
  awardCount,
  onCancel,
  onConfirm,
}: SubmitConfirmDialogProps) {
  const titleId = useId();
  const descId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    confirmRef.current?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !submitting) {
        e.preventDefault();
        onCancel();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, submitting, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center px-5"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/70"
        aria-label="Dismiss confirmation"
        disabled={submitting}
        onClick={onCancel}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative z-[1] w-full max-w-md border border-[var(--rule)] bg-surface px-6 py-6 shadow-[0_24px_48px_-28px_rgba(0,0,0,0.85)]"
      >
        <h2
          id={titleId}
          className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink"
        >
          Submit your ballot?
        </h2>
        <p id={descId} className="mt-3 text-sm leading-relaxed text-ink-muted">
          You are about to submit {awardCount} award
          {awardCount === 1 ? "" : "s"}. After you confirm, your votes are final
          and cannot be changed.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            ref={confirmRef}
            type="button"
            disabled={submitting}
            onClick={onConfirm}
            className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ground transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Submitting…" : "Confirm submit"}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={onCancel}
            className="inline-flex border border-[var(--rule)] px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted transition-colors hover:border-gold/40 hover:text-ink disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
