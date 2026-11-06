"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { DivisionLogo } from "@/components/brand-logos";
import {
  AwardVoteSection,
  type VoteSelection,
} from "@/components/vote/award-vote-section";
import { BallotProgress } from "@/components/vote/ballot-progress";
import { SubmitConfirmDialog } from "@/components/vote/submit-confirm-dialog";
import {
  ApiRequestError,
  ballotTokenStorageKey,
  getBallot,
  submitVotes,
} from "@/lib/api";
import { companyLabel, formatDateTime } from "@/lib/format";
import type { Ballot, BallotAward, VoteSubmitItem } from "@/lib/types";

type BallotShellProps = {
  year: number;
  yearTitle: string;
  initialToken: string | null;
};

type LoadState =
  | { status: "loading" }
  | { status: "ready"; ballot: Ballot }
  | { status: "error"; message: string; code?: number };

function selectionFromAward(award: BallotAward): VoteSelection {
  const vote = award.current_vote;
  if (!vote) return null;
  if (vote.nominee_id != null) {
    return { kind: "nominee", nominee_id: vote.nominee_id };
  }
  if (vote.selected_person_id != null) {
    return {
      kind: "person",
      selected_person_id: vote.selected_person_id,
      display_name: vote.selected_person_name ?? "Selected colleague",
    };
  }
  return null;
}

function selectionsFromBallot(ballot: Ballot): Record<string, VoteSelection> {
  const next: Record<string, VoteSelection> = {};
  for (const award of ballot.awards) {
    next[award.slug] = selectionFromAward(award);
  }
  return next;
}

function groupAwards(awards: BallotAward[]) {
  const company = awards.filter((a) => a.division !== "shared");
  const shared = awards.filter((a) => a.division === "shared");
  return { company, shared };
}

function readSessionToken(year: number): string | null {
  try {
    return sessionStorage.getItem(ballotTokenStorageKey(year));
  } catch {
    return null;
  }
}

function writeSessionToken(year: number, token: string) {
  try {
    sessionStorage.setItem(ballotTokenStorageKey(year), token);
  } catch {
    // private mode
  }
}

function stripTokenFromUrl() {
  try {
    const url = new URL(window.location.href);
    if (!url.searchParams.has("token")) return;
    url.searchParams.delete("token");
    const search = url.searchParams.toString();
    const clean = `${url.pathname}${search ? `?${search}` : ""}${url.hash}`;
    window.history.replaceState({}, "", clean);
  } catch {
    // ignore
  }
}

function useBallotToken(year: number, initialToken: string | null): string | null {
  const fromUrl = initialToken?.trim() || null;

  const fromSession = useSyncExternalStore(
    () => () => {},
    () => (fromUrl ? fromUrl : readSessionToken(year)),
    () => fromUrl,
  );

  useEffect(() => {
    if (!fromUrl) return;
    writeSessionToken(year, fromUrl);
    // Email deep-link handoff: keep token in sessionStorage, not the shareable URL.
    stripTokenFromUrl();
  }, [year, fromUrl]);

  return fromUrl ?? fromSession;
}

export function BallotShell({
  year,
  yearTitle,
  initialToken,
}: BallotShellProps) {
  const token = useBallotToken(year, initialToken);
  const [load, setLoad] = useState<LoadState | null>(
    token ? { status: "loading" } : null,
  );
  const [selections, setSelections] = useState<Record<string, VoteSelection>>(
    {},
  );
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token?.trim()) return;
    let cancelled = false;

    queueMicrotask(() => {
      if (cancelled) return;
      setLoad({ status: "loading" });
      setConfirmOpen(false);
      setSubmitError(null);
    });

    void getBallot(year, token.trim())
      .then((ballot) => {
        if (cancelled) return;
        setLoad({ status: "ready", ballot });
        setSelections(selectionsFromBallot(ballot));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof ApiRequestError
            ? err.message
            : "Could not load your ballot.";
        const code = err instanceof ApiRequestError ? err.status : undefined;
        setLoad({ status: "error", message, code });
      });

    return () => {
      cancelled = true;
    };
  }, [token, year, reloadKey]);

  const answered = useMemo(() => {
    if (load?.status !== "ready") return 0;
    return load.ballot.awards.filter((a) => selections[a.slug] != null).length;
  }, [load, selections]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (load?.status !== "ready" || !token) return;
    if (load.ballot.is_submitted || !load.ballot.writes_allowed) return;

    setAttemptedSubmit(true);
    const missing = load.ballot.awards.filter((a) => selections[a.slug] == null);
    if (missing.length) {
      setSubmitError(
        "Answer every award before submitting. Incomplete ballots are not saved.",
      );
      const first = missing[0];
      if (first) {
        const el = document.getElementById(`award-${first.slug}`);
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
        el?.focus({ preventScroll: true });
      }
      return;
    }

    setSubmitError(null);
    setConfirmOpen(true);
  }

  async function confirmSubmit() {
    if (load?.status !== "ready" || !token) return;
    if (load.ballot.is_submitted || !load.ballot.writes_allowed) return;

    const votes: VoteSubmitItem[] = load.ballot.awards.map((award) => {
      const sel = selections[award.slug];
      if (sel?.kind === "nominee") {
        return { award_slug: award.slug, nominee_id: sel.nominee_id };
      }
      if (sel?.kind === "person") {
        return {
          award_slug: award.slug,
          selected_person_id: sel.selected_person_id,
        };
      }
      return { award_slug: award.slug };
    });

    setSubmitting(true);
    setSubmitError(null);
    try {
      const updated = await submitVotes(year, token, votes);
      setLoad({ status: "ready", ballot: updated });
      setSelections(selectionsFromBallot(updated));
      setConfirmOpen(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : "Submit failed. Please try again.";
      setSubmitError(message);
      setConfirmOpen(false);
      window.requestAnimationFrame(() => {
        document.getElementById("ballot-submit-error")?.focus();
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (!token?.trim()) {
    return (
      <BallotFrame title="Ballot">
        <div className="space-y-4 text-base leading-relaxed text-ink-muted">
          <p>
            Voting is by personal email link only. There is no public ballot
            for {yearTitle}.
          </p>
          <p>
            Open the invite from your Incel Group inbox. If you lost it, ask HR
            or the awards committee for a fresh link.
          </p>
        </div>
        <BackLink year={year} />
      </BallotFrame>
    );
  }

  if (!load || load.status === "loading") {
    return (
      <BallotFrame title="Ballot">
        <p className="text-base text-ink-muted" aria-live="polite">
          Loading your ballot…
        </p>
      </BallotFrame>
    );
  }

  if (load.status === "error") {
    const invalid =
      load.code === 401 || load.code === 403 || load.code === 404;
    return (
      <BallotFrame title="Ballot">
        <div
          className="border border-[var(--danger)] bg-[color-mix(in_srgb,var(--danger)_14%,var(--surface))] px-4 py-4"
          role="alert"
        >
          <p className="font-[family-name:var(--font-display)] text-lg text-ink">
            {invalid ? "This ballot link is not valid" : "Ballot unavailable"}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">
            {load.message}
          </p>
          {invalid ? (
            <p className="mt-3 text-sm text-ink-muted">
              Ask HR or the awards committee for a fresh invite if you need a
              new link.
            </p>
          ) : (
            <button
              type="button"
              onClick={() => setReloadKey((k) => k + 1)}
              className="mt-4 inline-flex bg-gradient-to-r from-gold to-gold-bright px-5 py-2.5 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ground hover:brightness-110"
            >
              Try again
            </button>
          )}
        </div>
        <BackLink year={year} />
      </BallotFrame>
    );
  }

  const { ballot } = load;
  const windowStatus = ballot.voting_window_status;
  const isSubmitted = Boolean(ballot.is_submitted);
  const canWrite = ballot.writes_allowed && !isSubmitted;
  const tooEarly = windowStatus === "upcoming";
  const isClosed =
    windowStatus === "closed" ||
    (!ballot.writes_allowed && !tooEarly && !isSubmitted);
  const { company, shared } = groupAwards(ballot.awards);
  const companyTitle =
    ballot.voter.company === "tourism"
      ? "Tourism awards"
      : ballot.voter.company === "global"
        ? "Global awards"
        : "Your company awards";

  return (
    <main className="mx-auto max-w-2xl px-5 py-12 sm:px-8 sm:py-16">
      <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.16em] text-ink-muted">
        {ballot.title}
      </p>
      <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink sm:text-4xl">
        Your ballot
      </h1>
      <p className="mt-3 text-base text-ink">
        {ballot.voter.display_name ||
          `${ballot.voter.first_name} ${ballot.voter.last_name}`.trim()}
        <span className="text-ink-muted">
          {" "}
          · {companyLabel(ballot.voter.company)}
          {ballot.voter.electorate === "executive"
            ? " · Voting as executive management"
            : ""}
        </span>
      </p>

      {isSubmitted ? (
        <div
          className="mt-8 border border-teal bg-[color-mix(in_srgb,var(--teal)_16%,var(--surface))] px-4 py-4"
          role="status"
        >
          <p className="font-[family-name:var(--font-display)] text-lg text-ink">
            Ballot submitted
          </p>
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">
            Thank you. Your votes are final
            {ballot.submitted_at
              ? ` (submitted ${formatDateTime(ballot.submitted_at)})`
              : ""}
            and cannot be changed.
          </p>
        </div>
      ) : null}

      {tooEarly ? (
        <WindowNotice
          tone="upcoming"
          title="Voting has not opened yet"
          body={`Ballots open ${formatDateTime(ballot.voting_opens_at)}. You can review this page; submissions unlock when voting starts.`}
        />
      ) : null}

      {isClosed ? (
        <WindowNotice
          tone="closed"
          title="Voting is closed"
          body={`The window closed ${formatDateTime(ballot.voting_closes_at)}. Your last saved choices are shown below when available.`}
        />
      ) : null}

      {!tooEarly && !isClosed && !isSubmitted ? (
        <p className="mt-6 text-sm text-ink-muted">
          Opens {formatDateTime(ballot.voting_opens_at)} · Closes{" "}
          {formatDateTime(ballot.voting_closes_at)}. Once submitted, votes
          cannot be edited. Tallies stay hidden until results are published.
        </p>
      ) : null}

      <div className="mt-8">
        <BallotProgress answered={answered} total={ballot.awards.length} />
      </div>

      <form onSubmit={handleSubmit} className="mt-10 space-y-12">
        {company.length ? (
          <AwardGroup
            title={companyTitle}
            plane={
              company[0]?.division === "tourism" ? "bg-tourism" : "bg-global"
            }
            division={
              company[0]?.division === "tourism" ? "tourism" : "global"
            }
          >
            {company.map((award) => (
              <AwardVoteSection
                key={award.slug}
                year={year}
                token={token}
                award={award}
                selection={selections[award.slug] ?? null}
                disabled={!canWrite || submitting}
                showError={attemptedSubmit}
                onChange={(sel) =>
                  setSelections((prev) => ({ ...prev, [award.slug]: sel }))
                }
              />
            ))}
          </AwardGroup>
        ) : null}

        {shared.length ? (
          <AwardGroup title="General awards" plane="bg-shared" division="shared">
            {shared.map((award) => (
              <AwardVoteSection
                key={award.slug}
                year={year}
                token={token}
                award={award}
                selection={selections[award.slug] ?? null}
                disabled={!canWrite || submitting}
                showError={attemptedSubmit}
                onChange={(sel) =>
                  setSelections((prev) => ({ ...prev, [award.slug]: sel }))
                }
              />
            ))}
          </AwardGroup>
        ) : null}

        {submitError ? (
          <p
            id="ballot-submit-error"
            tabIndex={-1}
            className="text-sm text-[var(--danger)] outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2"
            role="alert"
          >
            {submitError}
          </p>
        ) : null}

        {canWrite ? (
          <div className="flex flex-wrap items-center gap-4 border-t border-[var(--rule)] pt-8">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex bg-gradient-to-r from-gold to-gold-bright px-6 py-3 font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-ground transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Submit votes
            </button>
            <p className="text-sm text-ink-muted">
              All awards are required. Submission is final — you cannot edit
              after confirming.
            </p>
          </div>
        ) : null}
      </form>

      <SubmitConfirmDialog
        open={confirmOpen}
        submitting={submitting}
        awardCount={ballot.awards.length}
        onCancel={() => {
          if (!submitting) setConfirmOpen(false);
        }}
        onConfirm={() => {
          void confirmSubmit();
        }}
      />

      <BackLink year={year} />
    </main>
  );
}

function BallotFrame({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto max-w-xl px-5 py-16 sm:px-8 sm:py-20">
      <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink">
        {title}
      </h1>
      <div className="mt-6 space-y-6">{children}</div>
    </main>
  );
}

function BackLink({ year }: { year: number }) {
  return (
    <p className="mt-10">
      <Link
        href={`/${year}`}
        className="thread-link font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-indigo"
      >
        Back to {year} hub
      </Link>
    </p>
  );
}

function WindowNotice({
  tone,
  title,
  body,
}: {
  tone: "upcoming" | "closed";
  title: string;
  body: string;
}) {
  const border =
    tone === "upcoming"
      ? "border-gold bg-[color-mix(in_srgb,var(--gold)_14%,var(--surface))]"
      : "border-[var(--rule)] bg-ground-deep";
  return (
    <div className={`mt-8 border px-4 py-4 ${border}`} role="status">
      <p className="font-[family-name:var(--font-display)] text-lg text-ink">
        {title}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">{body}</p>
    </div>
  );
}

function AwardGroup({
  title,
  plane,
  division,
  children,
}: {
  title: string;
  plane: string;
  division: "tourism" | "global" | "shared";
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <span className={`h-7 w-1.5 ${plane}`} aria-hidden />
        <DivisionLogo
          division={division}
          size={52}
          className="h-12 w-auto shrink-0 sm:h-14"
        />
        <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink">
          {title}
        </h2>
      </div>
      <div className="axial-rule mb-6" />
      <div className="space-y-5">{children}</div>
    </div>
  );
}
