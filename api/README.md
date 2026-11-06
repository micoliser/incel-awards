# Incel Awards API

Django + DRF backend for the Incel Employee Awards app.

## Phase status

- **Phase 0** — Scaffold (settings, CORS, health) ✅
- **Phase 1** — Models, admin, classification, 2026 seed ✅
- Phase 2+ — Public read API, voting, email (not yet)

## Setup

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Default .env.example uses USE_SQLITE=true for local/dev
```

## Migrate / seed / test

```bash
python manage.py migrate
python manage.py seed_year_2026
python manage.py test
```

Health check: `GET /api/v1/health/`

Admin: `/admin/` (create a superuser with `createsuperuser`).

## Apps

| App | Role |
|---|---|
| `people` | `OrgPerson` + classification helpers |
| `awards` | Year / awards / criteria / nominees / notification config + 2026 seed |
| `voting` | `BallotToken`, `BallotInviteDelivery`, `Vote` (models only in Phase 1) |
| `emails` | Placeholder for Phase 4 |

## PostgreSQL

Set `USE_SQLITE=false` (or unset) and provide `DB_*` vars in `.env`.
