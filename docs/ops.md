# Operations runbook — Incel Awards

Season lifecycle for the Django API (`api/`). Frontend ballot links use
`{FRONTEND_BASE_URL}/{year}/vote?token=...`.

## Env checklist

Copy `api/.env.example` → `api/.env`. Critical keys:

| Variable | Purpose |
|---|---|
| `DJANGO_DEBUG` / `DJANGO_SECRET_KEY` / `DJANGO_ALLOWED_HOSTS` | Core Django; production validation when `DEBUG=False` |
| `USE_SQLITE` / `DB_*` | SQLite locally; PostgreSQL in production (`DB_HOST` set) |
| `FRONTEND_BASE_URL` | Ballot + invite links |
| `CORS_ALLOWED_ORIGINS` | Production CORS (DEBUG allows all) |
| `ORG_USERS_API_BASE_URL` / `ORG_USERS_API_TOKEN` / `ORG_USERS_API_AUTH_SCHEME` | Org roster sync — `GET {base}/api/v1/external/users` with `Authorization: Bearer <token>` |
| `DEV_ORG_USERS_ENABLED` | Local fake directory at the same `/api/v1/external/users` path |
| `EMAIL_*` / `EMAIL_ENABLED` / `EMAIL_DEBUG` | Console locally; SMTP in production |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis for Celery worker + beat |
| `SEASON_TICK_SECONDS` | How often beat runs automation (default 60 local / 300 prod) |
| `BALLOT_THROTTLE_*` | Ballot API rate limits |

## Processes to run

| Process | Command | Role |
|---|---|---|
| API | `python manage.py runserver 8000` | Admin, ballot API, local fake org users |
| Celery worker | `celery -A config worker -l info` | Runs sync / tokens / invites (emails print here locally) |
| Celery beat | `celery -A config beat -l info` | Schedules `season_tick` every `SEASON_TICK_SECONDS` |
| Frontend | `npm run dev` or `npm start` in `frontend/` | Public site + ballot UI |

Redis must be running (`redis-cli ping` → `PONG`).

## What `season_tick` does automatically

Every tick (idempotent):

1. **Sync** people from `ORG_USERS_API_*`
2. **Generate** missing ballot tokens for active years
3. **Dispatch eligibility notices** when `now >= voting_opens_at - offset` (categories only; no nominees)
4. **Dispatch vote invites** when `now >= voting_opens_at - offset` (personal ballot links)
5. **Advance status** `scheduled → voting` at open, `voting → closed` at close

Offsets are per notification config in admin (defaults: eligibility **10 minutes**, vote invite **60 minutes**).

You do **not** manually sync, mint tokens, or send emails for a normal season.

Manual one-shot (same logic as beat):

```bash
python manage.py run_season_tick
```

## Local end-to-end test (admin-driven)

`.env` should already point at the fake directory:

```
ORG_USERS_API_BASE_URL=http://127.0.0.1:8000
ORG_USERS_API_TOKEN=dev-org-token
ORG_USERS_API_AUTH_SCHEME=Bearer
DEV_ORG_USERS_ENABLED=True
EMAIL_ENABLED=True
EMAIL_DEBUG=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

1. Start Redis, API, Celery worker, Celery beat, frontend.
2. Seed once if needed: `python manage.py seed_year_2026`
3. Django admin → **Award years** → 2026:
   - Set `voting_opens_at` ~15 minutes from now
   - Set `voting_closes_at` later the same day
   - Status: `scheduled`
   - Inline **eligibility notice** config: `offset_minutes_before_open` = `10`, enabled
   - Inline **vote invite** config: `offset_minutes_before_open` = `5`, enabled
4. Watch the **Celery worker** terminal. At `opens − 10 minutes` you should see
   eligibility emails (categories only). At `opens − 5 minutes`, vote invite
   emails with `/2026/vote?token=...` links. Copy a ballot link from the invite.
5. Open the link in the browser and vote. After `voting_opens_at`, status flips
   to `voting` on the next tick.
6. After close time, status becomes `closed`.

## Results: committee first, public after ceremony

Public `/[year]/results` stays closed until you set **`results_published_at`**.

**Committee preview (private):**
1. Django admin → **Award years** → 2026
2. Copy **Committee preview URL** (`/{year}/results?preview=…`)
3. From that page (or admin), open **Full voting audit**
   (`/{year}/results/audit?preview=…`) for ballots, weighted maths, and change logs
4. Share only with committee members

The audit endpoint **always** requires the preview token — even after public
publish. Publishing only unlocks the winners page, never individual ballots.

Do **not** set `results_published_at` until after the ceremony. When you do, the
same `/[year]/results` page becomes public (no preview query needed).

Rotate the preview token from the year admin action if a link leaks.

## Production go-live

Full CapRover / GHCR steps: **[DEPLOYMENT.md](./DEPLOYMENT.md)**.

1. Set `ORG_USERS_API_*` to the real portal with `ORG_USERS_API_AUTH_SCHEME=Bearer`
   (disable `DEV_ORG_USERS_ENABLED`).
2. SMTP + `EMAIL_ENABLED=True`, `EMAIL_DEBUG=False`.
3. CapRover apps: API + frontend + Celery worker + Celery beat (shared Postgres/Redis).
4. Admin: set open/close; confirm eligibility notice offset (default 10 min) and
   vote invite offset (often 60 min).
5. After close: publish `results_published_at`.

See `api/.env.example` for the full production variable checklist.

## Opening a new year

1. Create / seed the new `AwardYear` and awards/nominees.
2. Ensure `eligibility_notice` and `vote_invite` notification configs exist
   (offset + audience).
3. Set open/close in admin; Celery handles sync, tokens, and emails.

Keep prior years `archived` after results; do not reuse ballot tokens across years.

## Useful checks

```bash
curl -s -H "Authorization: Bearer dev-org-token" -H "Accept: application/json" \
  http://127.0.0.1:8000/api/v1/external/users | head
python manage.py run_season_tick
python manage.py dispatch_eligibility_notices --year 2026 --force
python manage.py dispatch_vote_invites --year 2026 --force
python manage.py test
```

Inspect **Ballot invite deliveries** (events `eligibility_notice` / `vote_invite`)
and **Vote audit logs** in admin after runs.
