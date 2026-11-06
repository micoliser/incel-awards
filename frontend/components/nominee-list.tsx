import type { Nominee } from "@/lib/types";

export function NomineeList({ nominees }: { nominees: Nominee[] }) {
  const confirmed = nominees.filter((n) => n.is_confirmed !== false);
  if (!confirmed.length) {
    return (
      <p className="text-sm text-ink-muted">
        Nominees will appear here when confirmed.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-[var(--rule)]">
      {confirmed.map((n) => (
        <li key={n.id} className="py-4">
          <p className="font-medium text-ink">{n.display_name}</p>
          {n.nominee_type === "department" ? (
            <p className="mt-1 font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              Department
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
