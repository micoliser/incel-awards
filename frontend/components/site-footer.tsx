export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-[var(--rule)] bg-[color-mix(in_srgb,var(--ground-deep)_70%,var(--ground))] text-ink-muted">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-12 sm:flex-row sm:items-end sm:justify-between sm:px-8">
        <div>
          <p className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
            Incel Group
          </p>
          <p className="mt-1 max-w-md text-sm text-ink-muted">
            Employee Awards for Tourism and Global — one season on the stage.
          </p>
        </div>
        <p className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.2em] text-gold">
          Internal recognition
        </p>
      </div>
    </footer>
  );
}
