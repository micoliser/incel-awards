# Frontend Implementation Plan (Next.js)

## Goals

- Year-scoped public overview pages (criteria, nominees, rules)
- Tokenized voting UX with no login screens
- Render awards from API config — avoid hardcoding 2026 rules in components
- Clean, professional corporate awards feel (follow existing Incel visual language when branding assets are available)

## App structure

```text
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                      # Home / overview
│   ├── years/
│   │   └── page.tsx                  # Optional archive list (or fold into home)
│   ├── [year]/
│   │   ├── layout.tsx                # Year chrome + fetch year meta
│   │   ├── page.tsx                  # Year hub
│   │   ├── awards/
│   │   │   ├── page.tsx              # All awards for year
│   │   │   └── [slug]/page.tsx      # Award detail
│   │   ├── vote/
│   │   │   └── page.tsx              # Ballot (?token=)
│   │   └── results/
│   │       └── page.tsx              # Published results
│   └── not-found.tsx
├── components/
│   ├── site-header.tsx
│   ├── site-footer.tsx
│   ├── year-status-badge.tsx
│   ├── award-card.tsx
│   ├── criteria-list.tsx
│   ├── nominee-list.tsx
│   ├── voting-rules-panel.tsx
│   └── vote/
│       ├── ballot-shell.tsx
│       ├── award-vote-section.tsx
│       ├── nominee-radio-group.tsx
│       ├── person-search-picker.tsx   # Foodie / Employees' Choice
│       └── ballot-progress.tsx
├── lib/
│   ├── api.ts                        # fetch helpers → Django API
│   ├── types.ts                      # shared TS types mirroring API
│   └── format.ts                     # dates, percentages
└── package.json
```

Route convention from product discussion:

```text
/                         overview
/{year}                   year hub          e.g. /2026
/{year}/awards            catalogue
/{year}/awards/{slug}     award detail
/{year}/vote?token=...    voting
/{year}/results           results
```

---

## Pages

### Home `/`

- Brand + what Employee Awards are
- CTA to **current year** (latest `status` in `scheduled`/`voting`/`closed`, or max year)
- List past years as archive links
- No nominee dump on home — keep it overview-only

### Year hub `/{year}`

- Year title, dates (opens / closes), status badge
- Short explanation of Tourism vs Global + shared awards
- Sections:
  - Company awards (Tourism / Global)
  - Shared awards
- Links into award details
- If voting open: “Have a ballot link? Open it from your email” (no public vote entry without token)

### Awards list `/{year}/awards`

- Filter chips: All / Tourism / Global / Shared
- Cards: name, division, voting mode label, nominee count

### Award detail `/{year}/awards/[slug]`

Data-driven sections from API:

1. Title + division badge
2. Description
3. **How voting works** (weights / all-staff / open) — from `voting_mode` + weights
4. **Criteria** list with percentages (hide if empty)
5. **Nominees** (confirmed only) with justification when present
6. Status note (voting not started / open / closed)

Do **not** special-case award slugs in UI except minor copy if needed. Prefer API fields.

### Vote `/{year}/vote?token=`

1. On load: `GET /api/v1/years/{year}/ballot/?token=`
2. States:
   - Missing/invalid token → error
   - Too early → countdown / opens-at message (still show who they are)
   - Open → ballot form
   - Closed → read-only summary of their choices if you want; else “voting closed”
3. Ballot content = only awards API returns for this voter
4. Group UI:
   - Your company awards (Tourism **or** Global block)
   - Shared awards
5. Controls:
   - Radio list for shortlist/weighted
   - Searchable person picker for open awards (`GET .../ballot/directory/?q=`)
6. Submit: `PUT .../ballot/votes/` with all selections (or per-section save)
7. Success: confirmation + optional “you can change votes until {closes_at}”

**Privacy:** never show tallies on this page during voting.

### Results `/{year}/results`

- If not published → friendly “Results not published yet”
- If published → per-award winner + optional percentages (especially weighted)
- Keep nominee runner-up display optional for v1

---

## API client

`lib/api.ts`:

- `API_BASE_URL` from `NEXT_PUBLIC_API_BASE_URL`
- Typed helpers: `getYear`, `getAwards`, `getAward`, `getBallot`, `submitVotes`, `searchDirectory`, `getResults`
- Server components for public pages (cache lightly)
- Client components for vote form (token in URL; prefer client fetch so token isn’t logged in RSC caches carelessly)

**Token handling**

- Read `token` from `searchParams`
- Keep in memory / sessionStorage for the vote session so navigations within vote UI don’t drop it
- Do not put token into public analytics events

---

## Types (sketch)

```ts
type Division = "tourism" | "global" | "shared";
type VotingMode = "weighted" | "staff_shortlist" | "staff_open";

type Award = {
  slug: string;
  name: string;
  description: string;
  division: Division;
  voting_mode: VotingMode;
  executive_weight: number | null;
  staff_weight: number | null;
  criteria: { label: string; weight_percent: number }[];
  nominees: {
    id: number;
    display_name: string;
    nominee_type: "person" | "department";
    justification?: string;
  }[];
};

type Ballot = {
  year: number;
  voter: {
    first_name: string;
    last_name: string;
    company: "tourism" | "global";
    electorate: "staff" | "executive";
  };
  window: { opens_at: string; closes_at: string; is_open: boolean };
  awards: (Award & {
    current_vote?: { nominee_id?: number; selected_person_id?: number };
  })[];
};
```

---

## UX details

- Progressive disclosure: year hub → award detail for reading; email link → vote for action
- Mobile-first ballot (many staff will vote on phones)
- Clear labels: “Tourism awards”, “Global awards”, “Company-wide awards”
- Show electorate only subtly (“Voting as executive management”) for weighted context — optional
- Autosave optional; at minimum one primary **Submit votes** with validation (every required award answered)
- Required vs optional: all returned awards should be required for a complete ballot unless product says otherwise

---

## Build phases (frontend)

1. **Scaffold** Next.js + env + basic layout
2. **Public pages** home / year / awards / award detail against mock or real read API
3. **Vote page** wired to ballot endpoints + person search
4. **Results page**
5. **Polish** loading/error empty states, accessibility (radios, focus), email deep-link QA

---

## Env

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Out of scope (frontend v1)

- Admin CMS in Next
- Generating tokens from the UI
- Live charts during voting
- Login / SSO pages

Admin operations stay in Django admin + management commands.
