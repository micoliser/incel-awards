# Incel Awards

Year-scoped employee awards platform for Incel Group (voting-first).

**Stack:** Next.js (`frontend/`) + Django REST Framework (`api/`) monorepo. Both layers exist and are wired for 2026 seasons (public pages, ballot token voting, results, invite email dispatch).

## Documentation

Start here: **[docs/README.md](./docs/README.md)**

| Doc | Contents |
|---|---|
| [Implementation plan](./docs/IMPLEMENTATION_PLAN.md) | Phases, layout, decisions |
| [Domain rules](./docs/domain-rules.md) | Eligibility, company split, 2026 award map, tallies |
| [API plan](./docs/api.md) | Models, endpoints, email (prospiz-style), commands |
| [Frontend plan](./docs/frontend.md) | Routes, pages, vote UX |
| [Ops runbook](./docs/ops.md) | Sync → tokens → voting window → invites → publish; 2027 open |

## Status

API through Phase 6 hardening (ballot/results, invite emails, rate limits, vote audit log). Frontend public pages + vote/results UX talk to the live API (fixture fallback when unreachable).

## Run locally

```bash
# API — http://127.0.0.1:8000
cd api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # USE_SQLITE=true is fine for local
python manage.py migrate
python manage.py seed_year_2026
python manage.py runserver 8000

# Frontend — http://localhost:3000
cd frontend
npm install
npm run dev
```

Set `FRONTEND_BASE_URL=http://localhost:3000` in `api/.env`. See [docs/ops.md](./docs/ops.md) for season go-live and env checklist.

## Reference

- `Employee Awards 2026 - Final Committee Nominations.pdf`
- Email pattern: `incel_prospiz` (`api/core/emails/`)
