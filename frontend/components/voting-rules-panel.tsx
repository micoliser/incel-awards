/** Same public copy for every award — no voting-mode or electorate details. */
export function VotingRulesPanel() {
  return (
    <div className="stage-panel px-5 py-5">
      <h2 className="font-[family-name:var(--font-display)] text-base tracking-tight text-ink">
        How voting works
      </h2>
      <p className="mt-3 max-w-prose text-sm text-ink">
        When voting opens, eligible colleagues cast one pick per award on their
        personal ballot.
      </p>
    </div>
  );
}
