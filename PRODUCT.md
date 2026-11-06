# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: Next.js App Router + TypeScript in `frontend/`, Django REST Framework in `api/` — matching the monorepo plan and sibling Incel apps (prospiz / portal). Styling approach to be set by DESIGN.md after the visual world is established (Tailwind acceptable).

## Users

- **Primary (voters):** Incel Group Nigeria staff (Tourism and Global divisions) who receive a unique ballot link by email. They vote on phones or desktops without logging in; eligibility and company gating are server-side.
- **Secondary (readers):** Same staff (and leadership) browsing public year overview, award criteria, and nominees before or during the season — no token required.
- **Operators (out of frontend v1 scope):** Committee / HR admins manage years, awards, nominees, and windows in Django admin.

*(Inferred from `docs/IMPLEMENTATION_PLAN.md`, `docs/frontend.md`, `docs/domain-rules.md`, and the Phase 0 brief.)*

## Product Purpose

Year-scoped **Incel Group Employee Awards**: a reusable season for each year (criteria, nominees, voting rules, email timing). Staff discover the season and awards publicly, then cast votes via opaque ballot tokens. Success for 2026 go-live: every eligible Nigeria person gets one working ballot link; Tourism/Global gating and weighted tallies match committee rules; results stay hidden until published.

*(Inferred from planning docs.)*

## Positioning

Config-driven award seasons hung off a year root — not a one-off 2026 hardcoded page. Voting uses **personal ballot links** (no SSO for voters). Company split (Tourism / Global / shared) is data-driven eligibility, not separate apps.

*(Inferred from implementation plan “Core design decisions”.)*

## Operating Context

- Corporate Nigeria org with **Tourism** and **Global** divisions; Dubai (`TOURISM_DUBAI`) excluded from this cycle.
- 2026 seeded from committee nominations PDF (`Employee Awards 2026 - Final Committee Nominations.pdf`).
- Ballot invites email ~1 hour before voting opens (configurable per year).
- Public overview → award detail for reading; email deep-link → vote for action.
- Frontend never decides eligibility or tallies; API re-validates.

*(Inferred from domain-rules and implementation plan.)*

## Capabilities and Constraints

**In scope for the public site (phased):**

- Year-scoped routes: home, year hub, awards catalogue, award detail, vote (`?token=`), results.
- Render awards from API config (division, voting_mode, weights, criteria, nominees).
- Tokenized ballot UX (later phases); no login screens for voters.

**Phase 0 (this build):** scaffold + Impeccable product/design foundation + route shells with fixture/stub data. No live API dependency; no real vote submission.

**Out of scope (v1 frontend):** Next admin CMS, token generation UI, live leaderboards during voting, SSO/login pages, inventing meme/“incel-internet” aesthetic.

**Undecided (product, later):** vote edit-until-close vs lock-on-submit (Phase 3 recommendation: editable until close).

*(Constraints from Phase 0 brief + frontend.md out-of-scope.)*

## Brand Commitments

- Company name: **Incel Group**.
- Product framing: **employee awards** — professional corporate awards atmosphere for a Nigeria org with Tourism + Global divisions.
- Explicit anti-aesthetic from the brief: not meme / incel-internet visual language.
- User frontend hard rules (binding): expressive fonts (not Inter/Roboto/Arial/system); avoid purple-on-white AI-slop, cream+terracotta cliché, broadsheet cliché; brand-first first viewport; no card soup in heroes; atmosphere over flat single-color grounds.

*(Explicit in Phase 0 brief.)*

## Evidence on Hand

- Planning docs under `docs/` (implementation, domain rules, API, frontend).
- `Employee Awards 2026 - Final Committee Nominations.pdf` (award/nominee source).
- No committed logo/brand asset pack in-repo yet — future work must not fabricate official marks; use typographic brand treatment until assets arrive.

## Product Principles

1. **Year is the season** — every public surface is year-scoped and config-driven.
2. **Progressive disclosure** — overview and criteria for everyone; voting only via personal link.
3. **Server authority** — UI reflects API truth; never invent eligibility or tallies client-side.
4. **Corporate dignity** — awards feel like a serious internal recognition moment, not a meme site.
5. **Reuse over hardcoding** — components render division/mode/criteria from data so 2027 does not fork the UI.

## Accessibility & Inclusion

No product-specific WCAG target locked yet. Default expectation: usable ballot on mobile (many staff vote on phones), clear focus states, semantic radios/labels when vote UX ships. *(Open — inferred as good practice, not a contracted standard.)*
