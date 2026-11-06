# Incel Awards — Documentation

Employee awards platform for Incel Group. Monorepo with **Next.js** (`frontend/`) and **Django REST Framework** (`api/`).

## Docs index

| Doc | Purpose |
|---|---|
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Phased build plan, repo layout, decisions, 2026 defaults |
| [domain-rules.md](./domain-rules.md) | Eligibility, company split, award map, tally rules |
| [api.md](./api.md) | Django apps, models, endpoints, email, sync, commands |
| [frontend.md](./frontend.md) | Next.js routes, pages, vote UX, API usage |
| [ops.md](./ops.md) | Season go-live runbook, env checklist, opening 2027 |

## Source inputs

- `Employee Awards 2026 - Final Committee Nominations.pdf` — 2026 nominees, criteria, weighted vote examples
- Org users API (Incel Portal / workspace) — voter roster
- Email pattern — mirror `incel_prospiz` (`BaseEmailService` + daemon threads + SMTP env flags)

## Quick product summary

- Year-scoped awards (`/2026/...`) with flexible per-year config
- No password login — unique ballot tokens emailed to eligible staff
- Tourism vs Global gating for company-divided awards; shared awards open to both
- Dubai (`TOURISM_DUBAI`) excluded
- Weighted exec + staff tallies for Employee / Supervisor / Department of the Year
