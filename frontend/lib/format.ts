import type { Division, VotingMode, YearStatus } from "@/lib/types";

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "TBD";
  try {
    return new Intl.DateTimeFormat("en-NG", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Africa/Lagos",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function divisionLabel(division: Division): string {
  switch (division) {
    case "tourism":
      return "Tourism";
    case "global":
      return "Global";
    case "shared":
      return "General";
  }
}

/** Brand line for award stage banners and similar surfaces. */
export function divisionCompanyName(division: Division): string {
  switch (division) {
    case "tourism":
      return "Incel Tourism";
    case "global":
      return "Incel Global";
    case "shared":
      return "Incel Group";
  }
}

export function votingModeLabel(mode: VotingMode): string {
  switch (mode) {
    case "weighted":
      return "Weighted vote";
    case "staff_shortlist":
      return "Staff shortlist";
    case "staff_open":
      return "Open popular vote";
  }
}

export function yearStatusLabel(status: YearStatus): string {
  switch (status) {
    case "draft":
      return "Preparing";
    case "scheduled":
      return "Upcoming";
    case "voting":
      return "Voting open";
    case "closed":
      return "Voting closed";
    case "archived":
      return "Archived";
  }
}

export function asNumber(value: number | string | null | undefined): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

export function percentLabel(fraction: number | string | null | undefined): string {
  const n = asNumber(fraction);
  if (n == null) return "n/a";
  return `${Math.round(n * 100)}%`;
}

export function scorePercentLabel(score: string | number | null | undefined): string {
  const n = asNumber(score);
  if (n == null) return "n/a";
  // Weighted tallies are 0-1 fractions; simple tallies are raw vote counts.
  if (n >= 0 && n <= 1) return `${Math.round(n * 1000) / 10}%`;
  return String(n);
}

export function companyLabel(company: "tourism" | "global" | string): string {
  if (company === "tourism") return "Tourism";
  if (company === "global") return "Global";
  return company;
}
