import type {
  ApiError,
  AuditFetch,
  Award,
  AwardYearDetail,
  AwardYearSummary,
  Ballot,
  DirectoryPerson,
  DirectorySearchResponse,
  ResultsFetch,
  VoteSubmitItem,
  YearAuditReport,
  YearResults,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

/**
 * Ballot tokens are secrets. Never log raw tokens, put them in share metadata,
 * or append them to analytics URLs. Prefer X-Ballot-Token for writes; query
 * ?token= is only for email deep-links (stripped from the URL after handoff).
 */
function flattenApiDetail(detail: unknown): string | undefined {
  if (detail == null) return undefined;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => flattenApiDetail(item))
      .filter((s): s is string => Boolean(s));
    return parts.length ? parts.join(" ") : undefined;
  }
  if (typeof detail === "object") {
    const obj = detail as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    const parts = Object.values(obj)
      .map((v) => flattenApiDetail(v))
      .filter((s): s is string => Boolean(s));
    return parts.length ? parts.join(" ") : undefined;
  }
  return String(detail);
}

export class ApiRequestError extends Error {
  status: number;
  code?: string;

  constructor({ status, detail, code }: ApiError) {
    super(detail);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

type FetchResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError | "network" | "disabled" };

async function rawFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<FetchResult<T>> {
  if (!API_BASE_URL) {
    return { ok: false, error: "disabled" };
  }

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
    });

    if (!res.ok) {
      let detail = res.statusText || "Request failed";
      let code: string | undefined;
      try {
        const body = (await res.json()) as {
          detail?: unknown;
          code?: string;
          votes?: unknown;
        };
        detail = flattenApiDetail(body.detail) ?? flattenApiDetail(body) ?? detail;
        code = body.code;
      } catch {
        // non-JSON error body
      }
      return { ok: false, error: { status: res.status, detail, code } };
    }

    return { ok: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, error: "network" };
  }
}

async function apiGetPublic<T>(path: string): Promise<T | null> {
  const result = await rawFetch<T>(path, {
    next: { revalidate: 60 },
  } as RequestInit);
  if (result.ok) return result.data;
  return null;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export function isApiConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

export async function listYears(): Promise<AwardYearSummary[]> {
  const data = await apiGetPublic<AwardYearSummary[]>("/years/");
  return data ?? [];
}

export async function getYear(year: number): Promise<AwardYearDetail | null> {
  return apiGetPublic<AwardYearDetail>(`/years/${year}/`);
}

export async function getAwards(year: number): Promise<Award[]> {
  const data = await apiGetPublic<Award[]>(`/years/${year}/awards/`);
  if (!data) return [];
  return data.map((a) => ({
    ...a,
    criteria: a.criteria ?? [],
    nominees: a.nominees ?? [],
  }));
}

export async function getAward(
  year: number,
  slug: string,
): Promise<Award | null> {
  const data = await apiGetPublic<Award>(`/years/${year}/awards/${slug}/`);
  if (!data) return null;
  return {
    ...data,
    criteria: data.criteria ?? [],
    nominees: data.nominees ?? [],
  };
}

export async function getBallot(year: number, token: string): Promise<Ballot> {
  if (!token.trim()) {
    throw new ApiRequestError({
      status: 401,
      detail: "Ballot token required.",
    });
  }

  const result = await rawFetch<Ballot>(
    `/years/${year}/ballot/?token=${encodeURIComponent(token)}`,
    { cache: "no-store" },
  );

  if (result.ok) return result.data;
  if (result.error === "disabled" || result.error === "network") {
    throw new ApiRequestError({
      status: 0,
      detail:
        result.error === "disabled"
          ? "Voting API is not configured. Set NEXT_PUBLIC_API_BASE_URL."
          : "Could not reach the voting API. Try again shortly.",
    });
  }
  throw new ApiRequestError(result.error);
}

export async function submitVotes(
  year: number,
  token: string,
  votes: VoteSubmitItem[],
): Promise<Ballot> {
  const result = await rawFetch<Ballot>(`/years/${year}/ballot/votes/`, {
    method: "PUT",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-Ballot-Token": token,
    },
    body: JSON.stringify({ votes }),
  });

  if (result.ok) return result.data;
  if (result.error === "disabled" || result.error === "network") {
    throw new ApiRequestError({
      status: 0,
      detail:
        result.error === "disabled"
          ? "Voting API is not configured."
          : "Could not reach the voting API. Try again shortly.",
    });
  }
  throw new ApiRequestError(result.error);
}

export async function searchDirectory(
  year: number,
  token: string,
  q: string,
): Promise<DirectoryPerson[]> {
  const result = await rawFetch<DirectorySearchResponse>(
    `/years/${year}/ballot/directory/?token=${encodeURIComponent(token)}&q=${encodeURIComponent(q)}`,
    { cache: "no-store" },
  );
  if (result.ok) return result.data.results ?? [];
  if (result.error === "disabled" || result.error === "network") {
    throw new ApiRequestError({
      status: 0,
      detail:
        result.error === "disabled"
          ? "Directory search is unavailable."
          : "Could not reach the voting API. Try again shortly.",
    });
  }
  throw new ApiRequestError(result.error);
}

export async function getResults(
  year: number,
  previewToken?: string | null,
): Promise<ResultsFetch> {
  const preview = (previewToken || "").trim();
  const qs = preview ? `?preview=${encodeURIComponent(preview)}` : "";
  const result = await rawFetch<YearResults>(`/years/${year}/results/${qs}`, {
    cache: "no-store",
  });

  if (result.ok) return { state: "ready", data: result.data };
  if (result.error === "disabled" || result.error === "network") {
    return { state: "unavailable" };
  }
  if (result.error.status === 403 || result.error.status === 404) {
    return { state: "unpublished" };
  }
  return { state: "unavailable" };
}

/** Committee-only; always requires preview token (never public). */
export async function getResultsAudit(
  year: number,
  previewToken?: string | null,
): Promise<AuditFetch> {
  const preview = (previewToken || "").trim();
  if (!preview) return { state: "forbidden" };
  const result = await rawFetch<YearAuditReport>(
    `/years/${year}/results/audit/?preview=${encodeURIComponent(preview)}`,
    { cache: "no-store" },
  );
  if (result.ok) return { state: "ready", data: result.data };
  if (result.error === "disabled" || result.error === "network") {
    return { state: "unavailable" };
  }
  if (result.error.status === 403 || result.error.status === 404) {
    return { state: "forbidden" };
  }
  return { state: "unavailable" };
}

/** Prefer scheduled/voting/closed, else highest year number. */
export async function getCurrentYear(): Promise<AwardYearSummary | null> {
  const years = await listYears();
  if (!years.length) return null;
  const preferred = years.find((y) =>
    ["scheduled", "voting", "closed"].includes(y.status),
  );
  if (preferred) return preferred;
  return [...years].sort((a, b) => b.year - a.year)[0] ?? null;
}

export const BALLOT_TOKEN_STORAGE_PREFIX = "incel-awards-ballot-token:";

export function ballotTokenStorageKey(year: number): string {
  return `${BALLOT_TOKEN_STORAGE_PREFIX}${year}`;
}
