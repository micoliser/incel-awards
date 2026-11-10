# Incel Awards — CapRover deployment guide

This follows the same pattern as **incel_prospiz** / **incel-portal**:

1. GitHub Actions builds images → **GHCR**
2. CapRover pulls those images and runs them
3. One **shared Postgres** (new database on the existing CapRover Postgres app)
4. Shared **Redis** (different DB index) for Celery

Domains below are placeholders — replace with whatever you attach in CapRover.

```text
captain....                     CapRover dashboard

awards.incelgroup.com           incel-awards-frontend   (port 3000)
awards-api.incelgroup.com       incel-awards-api        (port 8000)

(no public domain)
incel-awards-celery-worker      same backend image
incel-awards-celery-beat        same backend image

srv-captain--<postgres-app>     shared Postgres
srv-captain--<redis-app>        shared Redis
```

---

## 0. Prerequisites

- CapRover cluster already running (same as prospiz/portal)
- GitHub repo for this project (push access)
- GHCR login on CapRover if packages are private  
  CapRover → **Cluster** → **Docker Registry** → `ghcr.io` + PAT with `read:packages`
- SMTP credentials that can send real awards emails
- Production org API token for  
  `GET {ORG_USERS_API_BASE_URL}/api/v1/external/users`

---

## 1. Create the awards database on the shared Postgres

SSH into CapRover / open a shell on the Postgres one-click app, then:

```sql
CREATE DATABASE incel_awards_db;
CREATE USER incel_awards_user WITH PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE incel_awards_db TO incel_awards_user;
\c incel_awards_db
GRANT ALL ON SCHEMA public TO incel_awards_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO incel_awards_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO incel_awards_user;
```

Note the CapRover internal hostname:

```text
DB_HOST=srv-captain--<your-postgres-app-name>
```

Example: if the Postgres CapRover app is named `incel-postgres`, host is  
`srv-captain--incel-postgres`.

Pick a Redis DB index **not** used by portal/prospiz (portal often uses `/15`):

```text
CELERY_BROKER_URL=redis://srv-captain--<redis-app>:6379/5
CELERY_RESULT_BACKEND=redis://srv-captain--<redis-app>:6379/5
```

---

## 2. Create four CapRover apps (one-time)

CapRover → **Apps** → **One-Click Apps / Create New App** (empty apps).

| CapRover app name | Image (after first CI run) | HTTP port | Has domain? |
|---|---|---|---|
| `incel-awards-api` | `ghcr.io/<github-owner>/incel-awards-backend:latest` | **8000** | Yes → `awards-api.…` |
| `incel-awards-frontend` | `ghcr.io/<github-owner>/incel-awards-frontend:latest` | **3000** | Yes → `awards.…` |
| `incel-awards-celery-worker` | same backend image | none (disable HTTP) | No |
| `incel-awards-celery-beat` | same backend image | none (disable HTTP) | No |

For each app → **Deployment** → **Method 3: Deploy via ImageName**

- Paste the image name above
- Enable **webhook** deploy and copy the webhook token/URL (needed for GitHub secrets)

### Start commands

**API** (`incel-awards-api`) — leave default Dockerfile CMD, or set:

```bash
sh -c "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile - --capture-output --log-level info"
```

**Celery worker** — override container start command:

```bash
celery -A config worker --loglevel=info
```

**Celery beat** — override container start command:

```bash
celery -A config beat --loglevel=info
```

**Frontend** — Dockerfile CMD is fine (`next start` on `0.0.0.0:3000`).

Enable HTTPS / force SSL on the two public apps after domains resolve.

---

## 3. Set CapRover environment variables

Set these on **api**, **celery-worker**, and **celery-beat** (same values on all three).

```dotenv
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<unique-32+-char-secret>
DJANGO_ALLOWED_HOSTS=awards-api.incelgroup.com,srv-captain--incel-awards-api
DJANGO_ADMIN_URL=admin/
DJANGO_SECURE_SSL_REDIRECT=True

USE_SQLITE=false
DB_NAME=incel_awards_db
DB_USER=incel_awards_user
DB_PASSWORD=<from step 1>
DB_HOST=srv-captain--<postgres-app>
DB_PORT=5432

FRONTEND_BASE_URL=https://awards.incelgroup.com
CORS_ALLOWED_ORIGINS=https://awards.incelgroup.com

# Origin of the portal API (not the workspace frontend).
ORG_USERS_API_BASE_URL=https://workspaceapi.incelgroup.com
ORG_USERS_API_TOKEN=<full raw incel_live_… key shown once at creation>
ORG_USERS_API_AUTH_SCHEME=Bearer
DEV_ORG_USERS_ENABLED=False

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-password>
DEFAULT_FROM_EMAIL=awards@incelgroup.com
EMAIL_SENDER_NAME=Incel Group Awards
EMAIL_ENABLED=True
EMAIL_DEBUG=False

CELERY_BROKER_URL=redis://srv-captain--<redis-app>:6379/5
CELERY_RESULT_BACKEND=redis://srv-captain--<redis-app>:6379/5
CELERY_TASK_ALWAYS_EAGER=False
SEASON_TICK_SECONDS=60
ORG_SYNC_SECONDS=3600

BALLOT_THROTTLE_RESOLVE=60/min
BALLOT_THROTTLE_VOTE=30/min
BALLOT_THROTTLE_DIRECTORY=60/min
```

Frontend app only needs:

```dotenv
NODE_ENV=production
HOSTNAME=0.0.0.0
```

`NEXT_PUBLIC_API_BASE_URL` is **baked into the image at build time** by CI.  
It is **not** fixed by CapRover runtime env. Rebuild the frontend image if the API domain changes.

---

## 4. GitHub repository secrets

Repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Value |
|---|---|
| `CAPROVER_SERVER` | CapRover URL, e.g. `https://captain.….incelgroup.com` |
| `CAPROVER_TOKEN_API` | Deploy token for `incel-awards-api` |
| `CAPROVER_TOKEN_FRONTEND` | Deploy token for `incel-awards-frontend` |
| `CAPROVER_TOKEN_CELERY_WORKER` | Deploy token for `incel-awards-celery-worker` |
| `CAPROVER_TOKEN_CELERY_BEAT` | Deploy token for `incel-awards-celery-beat` |

`GITHUB_TOKEN` is provided automatically for pushing to GHCR.

---

## 5. First deploy

1. Commit and push Dockerfiles + workflow (already in this repo layout).
2. Push to `main` **or** run **Actions → CI/CD → Run workflow**.
3. Confirm workflow:
   - tests pass
   - images appear under GitHub → Packages (`incel-awards-backend`, `incel-awards-frontend`)
   - CapRover deploy steps succeed
4. Open CapRover app logs:
   - API should show migrate + gunicorn listening on 8000
   - Worker/beat should show Celery ready
5. Smoke checks:

```bash
curl -sS https://awards-api.incelgroup.com/api/v1/health/
curl -sSI https://awards.incelgroup.com/
```

---

## 6. Post-deploy application setup (for real email test)

1. Create a Django superuser (one-time), from CapRover API app **one-shot command** or exec:

```bash
python manage.py createsuperuser
```

2. Open `https://awards-api.incelgroup.com/admin/`
3. Create / configure **Award year 2026**:
   - Set `voting_opens_at` / `voting_closes_at` for your test window
   - Status: `scheduled`
   - Notification configs:
     - **eligibility_notice** → e.g. `10` minutes before open
     - **vote_invite** → e.g. `5`–`60` minutes before open
4. Seed / refresh the 2026 catalogue (idempotent; removes retired slugs such as
   Supervisor of the Year and shared Rookie, and replaces Leadership / Rookie with
   Tourism + Global splits):

```bash
python manage.py seed_year_2026
```

   Expect **14** awards (6 weighted including both leadership awards, 6 shortlist
   including both Rookie awards, 2 open). Spot-check that Tourism staff see
   **Rookie (Tourism)** only and Global staff see **Rookie (Global)** only, while
   both ballots include **Department of the Year (Tourism + Global)** and
   **Excellent Leadership (Tourism + Global)**.

5. Confirm org sync + mail tick (one-shots):

```bash
python manage.py run_season_tick --sync-only
python manage.py run_season_tick --mail-only
```

Or full pipeline: `python manage.py run_season_tick`.  
Watch **celery-worker** logs for invite / eligibility SMTP sends. Set CapRover
`SEASON_TICK_SECONDS=60` and `ORG_SYNC_SECONDS=3600` on api, worker, and beat.

6. When invites go out, open a ballot link from the email and vote end-to-end.

### Re-running a live test (wipe slate)

Changing only the voting window does **not** resend emails — successful
`BallotInviteDelivery` rows block re-send. After deploying a build that includes
`reset_season_for_testing`:

```bash
docker exec -it srv-captain--incel-awards-api \
  python manage.py reset_season_for_testing --year 2026 --confirm \
  --opens-in-minutes 15 --window-minutes 30 \
  --eligibility-offset 10 --invite-offset 5 \
  --rotate-preview-token
```

That clears votes, audit logs, invite deliveries, unlocks ballots, unpublishes
results, and schedules a fresh window. Awards / nominees / org people are kept.

---

## 7. Ongoing deploys

Same as prospiz:

```text
git push origin main
```

That runs tests → builds GHCR images → CapRover webhooks pull `:latest`.

Manual rebuild only (no CapRover) or custom API URL:

- Actions → **CI/CD** → **Run workflow**
- Set `frontend_api_base_url` if your API domain differs
- Set `deploy=false` if you only want images

---

## 8. Rollback

1. In GHCR, note a previous working image digest/tag (commit SHA tags are published).
2. CapRover app → Deployment → Method 3 → set image to  
   `ghcr.io/<owner>/incel-awards-backend:<sha>` (and frontend similarly) → deploy webhook.
3. Or re-run CI on the good commit and redeploy.

---

## Troubleshooting

| Symptom | Likely fix |
|---|---|
| API won’t start / ImproperlyConfigured | Missing prod env (`DJANGO_SECRET_KEY`, `DB_PASSWORD`, HTTPS `FRONTEND_BASE_URL`) |
| 502 on API domain | Container port must be **8000**; check migrate/gunicorn logs |
| Frontend calls localhost API | Rebuild frontend image with correct `NEXT_PUBLIC_API_BASE_URL` |
| No emails | `EMAIL_ENABLED=True`, SMTP vars set, **worker + beat** both running |
| Season mail never fires | Beat must schedule `emails.season_tick`; set `SEASON_TICK_SECONDS=60` (not only `ORG_SYNC_SECONDS`) |
| Org roster stale | Beat must schedule `emails.org_sync_tick`; check `ORG_SYNC_SECONDS` + workspace API token |
| Org sync 401/404 | Use `ORG_USERS_API_BASE_URL=https://workspaceapi.incelgroup.com` (not `workspace.…`) + full raw Bearer key; set these in CapRover App Configs (not only local `.env.production`) |
| DB connection refused | `DB_HOST=srv-captain--<exact-postgres-app-name>` |

---

## Local vs production reminder

| | Local | CapRover |
|---|---|---|
| API | `runserver` | gunicorn in `incel-awards-api` |
| Frontend | `npm run dev` | Next container |
| Org users | fake `/api/v1/external/users` | real workspace API |
| Email | console backend | SMTP |
| Automation | local Redis + celery worker/beat | CapRover worker + beat apps |

Files that power this flow:

- `api/Dockerfile`, `frontend/Dockerfile`
- `.github/workflows/ci-cd.yml`
- `api/.env.example` / `frontend/.env.example` (variable reference)
