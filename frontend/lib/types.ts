/** Shared TypeScript types mirroring Django API payloads. */

export type Division = "tourism" | "global" | "shared";
export type VotingMode = "weighted" | "staff_shortlist" | "staff_open";
export type YearStatus = "draft" | "scheduled" | "voting" | "closed" | "archived";
export type Company = "tourism" | "global" | "excluded";
export type Electorate = "staff" | "executive" | "ineligible";
export type NomineeType = "person" | "department";
export type VotingWindowStatus = "upcoming" | "open" | "closed" | string;

export type AwardCriterion = {
  id?: number;
  label: string;
  weight_percent: number | string;
  sort_order?: number;
};

export type Nominee = {
  id: number;
  display_name: string;
  nominee_type: NomineeType;
  justification?: string;
  basis_for_nomination?: string;
  is_confirmed?: boolean;
  sort_order?: number;
};

/** List payload omits criteria/nominees; detail includes them. */
export type Award = {
  year?: number;
  slug: string;
  name: string;
  description: string;
  /** One ideal-winner trait per line; empty when the deck has none. */
  ideal_winner?: string;
  division: Division;
  voting_mode: VotingMode;
  executive_weight: number | string | null;
  staff_weight: number | string | null;
  sort_order?: number;
  is_active?: boolean;
  voting_rules?: {
    division: Division;
    mode: VotingMode;
    executive_weight: number | string | null;
    staff_weight: number | string | null;
  };
  voting_window_status?: VotingWindowStatus;
  criteria?: AwardCriterion[];
  nominees?: Nominee[];
};

export type AwardYearSummary = {
  year: number;
  title: string;
  slug: string;
  status: YearStatus;
  voting_opens_at: string | null;
  voting_closes_at: string | null;
  results_published_at?: string | null;
  description?: string;
};

export type AwardYearDetail = AwardYearSummary & {
  awards_count: number;
  confirmed_nominees_count?: number;
  voting_window_status?: VotingWindowStatus;
  description: string;
};

export type BallotVote = {
  award_slug?: string;
  nominee_id?: number | null;
  selected_person_id?: number | null;
  selected_person_name?: string | null;
  electorate_at_vote?: Electorate;
  updated_at?: string;
};

export type BallotAward = {
  slug: string;
  name: string;
  description: string;
  ideal_winner?: string;
  division: Division;
  voting_mode: VotingMode;
  executive_weight: number | string | null;
  staff_weight: number | string | null;
  sort_order?: number;
  criteria: AwardCriterion[];
  nominees: Nominee[];
  current_vote: BallotVote | null;
};

export type BallotVoter = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  company: Company;
  electorate: Electorate;
  department_name?: string;
};

export type Ballot = {
  year: number;
  title: string;
  status: YearStatus;
  voting_opens_at: string | null;
  voting_closes_at: string | null;
  voting_window_status: VotingWindowStatus;
  writes_allowed: boolean;
  is_submitted: boolean;
  submitted_at: string | null;
  voter: BallotVoter;
  awards: BallotAward[];
  votes: BallotVote[];
};

export type VoteSubmitItem = {
  award_slug: string;
  nominee_id?: number;
  selected_person_id?: number;
};

export type TallyNominee = {
  nominee_id: number | null;
  selected_person_id: number | null;
  display_name: string;
  score: string;
  exec_votes: number;
  staff_votes: number;
  total_votes: number;
  is_winner: boolean;
  is_tie: boolean;
};

export type AwardResult = {
  award_id: number;
  award_slug: string;
  voting_mode: VotingMode;
  eligible_exec_count: number;
  nominees: TallyNominee[];
  winners: TallyNominee[];
  /** Joined client-side from public awards catalogue when available. */
  award_name?: string;
  division?: Division;
};

export type YearResults = {
  year: number;
  title: string;
  results_published_at: string | null;
  /** True when loaded via committee preview token (not yet public). */
  preview?: boolean;
  awards: AwardResult[];
};

export type DirectoryPerson = {
  id: number;
  first_name: string;
  last_name: string;
  display_name: string;
  department_name?: string;
  company?: Company;
};

export type DirectorySearchResponse = {
  count: number;
  results: DirectoryPerson[];
};

export type ApiError = {
  status: number;
  detail: string;
  code?: string;
};

export type ResultsFetch =
  | { state: "ready"; data: YearResults }
  | { state: "unpublished" }
  | { state: "unavailable" };

export type AuditNomineeRow = {
  nominee_id: number | null;
  selected_person_id: number | null;
  display_name: string;
  exec_votes: number;
  staff_votes: number;
  total_votes: number;
  exec_share: string;
  staff_share: string;
  score: string;
  score_display: string;
  formula: string;
  is_winner: boolean;
  is_tie: boolean;
};

export type AuditBallotRow = {
  voter_id: number;
  voter_name: string;
  voter_email: string;
  voter_company: string;
  voter_department?: string;
  electorate_at_vote: string;
  choice_kind: string;
  choice_name: string;
  nominee_id: number | null;
  selected_person_id: number | null;
  created_at: string;
  updated_at: string;
  was_changed: boolean;
};

export type AuditChangeRow = {
  action: string;
  voter_name: string;
  voter_email: string;
  previous: string;
  new: string;
  created_at: string;
};

export type AuditAward = {
  award_id: number;
  award_slug: string;
  award_name: string;
  division: Division;
  voting_mode: VotingMode;
  description: string;
  votes_cast: number;
  calculation: Record<string, unknown>;
  nominees: AuditNomineeRow[];
  winners: AuditNomineeRow[];
  ballots: AuditBallotRow[];
  vote_changes: AuditChangeRow[];
};

export type YearAuditReport = {
  year: number;
  title: string;
  status: YearStatus;
  voting_opens_at: string | null;
  voting_closes_at: string | null;
  results_published_at: string | null;
  summary: {
    awards_count: number;
    ballots_issued: number;
    ballots_revoked: number;
    ballots_active: number;
    unique_voters: number;
    total_votes_cast: number;
    participation_rate: string;
    weighted_awards: number;
    shortlist_awards: number;
    open_awards: number;
  };
  methodology: {
    weighted: { title: string; steps: string[]; note: string };
    staff_shortlist: { title: string; steps: string[] };
    staff_open: { title: string; steps: string[] };
  };
  awards: AuditAward[];
};

export type AuditFetch =
  | { state: "ready"; data: YearAuditReport }
  | { state: "forbidden" }
  | { state: "unavailable" };
