# API Implementation Plan (Django + DRF)

## App layout

```text
api/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── people/                 # Org sync + classification
│   ├── models.py           # OrgPerson
│   ├── services/
│   │   ├── org_client.py   # HTTP client to company users API
│   │   ├── classify.py     # company + electorate + nigeria eligibility
│   │   └── sync.py
│   └── management/commands/sync_org_people.py
├── awards/                 # Year / award / criteria / nominees
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── management/commands/seed_year_2026.py
├── voting/                 # Tokens, votes, tallies
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── services/
│   │   ├── tokens.py
│   │   ├── eligibility.py
│   │   └── tally.py
│   └── admin.py
├── emails/                 # Mimic incel_prospiz
│   ├── config.py
│   ├── services/
│   │   ├── base.py
│   │   └── vote_invite_emails.py
│   ├── templates/emails/
│   │   ├── base_email.html
│   │   └── vote_invite.html
│   └── management/commands/
│       ├── dispatch_vote_invites.py
│       └── test_vote_invite_email.py
├── manage.py
└── requirements.txt
```

Optional: single `core` app like prospiz if you prefer fewer apps; split above keeps voting/awards/people clear.

---

## Models

### `people.OrgPerson`

Local snapshot of org directory users.

| Field | Type | Notes |
|---|---|---|
| `external_id` | int, unique | Portal user `id` |
| `email` | EmailField, indexed | |
| `first_name`, `last_name` | CharField | |
| `is_active` | bool | From source |
| `role_code` | CharField | `STAFF`, `ED`, `MD`, … |
| `role_name` | CharField | Display |
| `department_code` | CharField | |
| `department_name` | CharField | |
| `unit_name` | CharField null | |
| `raw_payload` | JSONField | Full API object for audit/debug |
| `company` | CharField | Cached: `tourism` \| `global` \| `excluded` |
| `electorate` | CharField | Cached: `staff` \| `executive` \| `ineligible` |
| `is_nigeria_eligible` | bool | Cached |
| `synced_at` | DateTimeField | |

Recompute `company` / `electorate` / `is_nigeria_eligible` on every sync via `people.services.classify`.

### `awards.AwardYear`

| Field | Type | Notes |
|---|---|---|
| `year` | PositiveInt, unique | e.g. 2026 |
| `title` | CharField | `Employee Awards 2026` |
| `slug` | slug | usually `str(year)` |
| `status` | CharField | `draft` \| `scheduled` \| `voting` \| `closed` \| `archived` |
| `voting_opens_at` | DateTimeField null | |
| `voting_closes_at` | DateTimeField null | |
| `results_published_at` | DateTimeField null | |
| `description` | TextField blank | Year overview copy |

### `awards.AwardNotificationConfig`

Flexible per-year email/notification rules (2026: one row for vote invites).

| Field | Type | Notes |
|---|---|---|
| `year` | FK AwardYear | |
| `event` | CharField | `vote_invite` (extensible) |
| `enabled` | bool | |
| `channel` | CharField | `email` |
| `audience` | CharField | `all_eligible` \| `staff_only` \| `executives_only` \| `tourism_only` \| `global_only` |
| `offset_minutes_before_open` | int | **2026 = 60** |
| `subject_template` | CharField | e.g. `Cast your vote — Incel Employee Awards {year}` |
| `extra` | JSONField blank | Future knobs |

Unique `(year, event)`.

### `awards.Award`

| Field | Type | Notes |
|---|---|---|
| `year` | FK AwardYear | |
| `slug` | slug | Unique per year |
| `name` | CharField | |
| `description` | TextField | |
| `division` | CharField | `tourism` \| `global` \| `shared` |
| `voting_mode` | CharField | `weighted` \| `staff_shortlist` \| `staff_open` |
| `executive_weight` | Decimal null | 0.30 etc.; only weighted |
| `staff_weight` | Decimal null | 0.70 etc. |
| `sort_order` | int | |
| `is_active` | bool | Hide unfinished awards (e.g. unconfirmed Rookie) |

Unique `(year, slug)`.

### `awards.AwardCriterion`

| Field | Type | Notes |
|---|---|---|
| `award` | FK Award | |
| `label` | CharField | |
| `weight_percent` | Decimal | Display weight |
| `sort_order` | int | |

### `awards.Nominee`

| Field | Type | Notes |
|---|---|---|
| `award` | FK Award | |
| `nominee_type` | CharField | `person` \| `department` |
| `display_name` | CharField | |
| `org_person` | FK OrgPerson null | Optional link |
| `justification` | TextField blank | Committee notes |
| `basis_for_nomination` | TextField blank | |
| `is_confirmed` | bool | Rookie soft confirmations |
| `sort_order` | int | |

Only `is_confirmed=True` nominees appear on ballots (seed unconfirmed as false until ready).

### `voting.BallotToken`

| Field | Type | Notes |
|---|---|---|
| `year` | FK AwardYear | |
| `person` | FK OrgPerson | |
| `token` | CharField unique | `secrets.token_urlsafe(32)` |
| `created_at` | DateTimeField | |
| `revoked_at` | DateTimeField null | |
| `last_accessed_at` | DateTimeField null | |

Unique `(year, person)`. URL: `{FRONTEND_BASE_URL}/{year}/vote?token=...`

### `voting.BallotInviteDelivery`

Idempotency / audit for emails.

| Field | Type | Notes |
|---|---|---|
| `token` | FK BallotToken | |
| `event` | CharField | `vote_invite` |
| `sent_at` | DateTimeField | |
| `status` | CharField | `sent` \| `failed` \| `skipped` |
| `error_message` | TextField blank | |

Unique `(token, event)` so cron can retry failures safely.

### `voting.Vote`

| Field | Type | Notes |
|---|---|---|
| `award` | FK Award | |
| `voter` | FK OrgPerson | |
| `nominee` | FK Nominee null | Shortlist / weighted |
| `selected_person` | FK OrgPerson null | Open awards |
| `electorate_at_vote` | CharField | Snapshot: staff/executive |
| `created_at`, `updated_at` | DateTimeField | |

Constraints:

- Unique `(award, voter)`
- Check: exactly one of `nominee` / `selected_person` set depending on award mode
- Application-level: voter eligible for award division; nominee belongs to award; window open

---

## Classification service (`people.services.classify`)

```python
DUBAI_DEPARTMENT = "TOURISM_DUBAI"
TOURISM_DEPARTMENT = "TOURISM"
EXEC_ROLE_CODES = {"ED", "MD"}
STAFF_ROLE_CODES = {"STAFF"}

def is_nigeria_eligible(person) -> bool: ...
def resolve_company(person) -> Literal["tourism", "global", "excluded"]: ...
def resolve_electorate(person) -> Literal["staff", "executive", "ineligible"]: ...
```

Tourism exceptions:

- `INTERNAL_CONTROL` + unit `Tourism Internal Control`
- `TRADING` + unit `Tourism Accounts`

---

## Endpoints

Base path: `/api/v1/`

### Public read

| Method | Path | Purpose |
|---|---|---|
| GET | `/years/` | List years (year, title, status, windows) |
| GET | `/years/{year}/` | Year detail + counts |
| GET | `/years/{year}/awards/` | Awards for year (public fields; no tallies) |
| GET | `/years/{year}/awards/{slug}/` | Award + criteria + confirmed nominees + voting rules summary |

Public award payload should include enough for overview pages: name, description, division, mode, weights, criteria, nominees (name + justification), status relative to voting window.

### Ballot (token auth)

Pass token via query `?token=` or header `X-Ballot-Token:`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/years/{year}/ballot/` | Resolve token → voter profile (name, company, electorate) + allowed awards + current votes + window status |
| PUT | `/years/{year}/ballot/votes/` | Upsert votes: `[{ "award_slug", "nominee_id" \| "selected_person_id" }, ...]` |
| GET | `/years/{year}/ballot/directory/` | Search Nigeria-eligible people for open awards (token required) |

`GET ballot` must **only** return awards the voter may vote on (division filter).

`PUT votes` behaviour:

- Reject if token revoked / person ineligible / outside window
- Validate each award against division + mode
- Upsert by `(award, voter)`
- Return updated ballot summary

### Results

| Method | Path | Purpose |
|---|---|---|
| GET | `/years/{year}/results/` | Per-award tallies + winners; **403/404 until** `results_published_at` set (unless staff admin key later) |

Internal/admin can use Django admin or a keyed endpoint for preview.

### Ops / admin (Django admin + commands preferred in v1)

Optional thin API later:

| Method | Path | Purpose |
|---|---|---|
| POST | `/internal/sync-org-people/` | Trigger sync (shared secret) |
| POST | `/internal/generate-tokens/{year}/` | Generate missing tokens |
| POST | `/internal/dispatch-invites/{year}/` | Trigger invite dispatch |

For v1, management commands are enough; protect any HTTP ops with `INTERNAL_API_KEY`.

---

## Tally service (`voting.services.tally`)

```python
def tally_award(award: Award) -> AwardTallyResult:
    """
    weighted:
      exec_value = award.executive_weight / eligible_exec_count_for_award
      staff_share = (votes/total_staff) * award.staff_weight
    staff_shortlist / staff_open:
      simple count; highest wins
    """
```

Eligible exec count = all Nigeria-eligible executives (ED/MD). Executives are not company-gated; staff still are for tourism/global.

Write unit tests from PDF scenarios (Employee Tourism 30/70, Supervisor 60/40, Department 50/50).

---

## Org sync

`python manage.py sync_org_people`

1. Fetch all users from org API (paginate if needed)
2. Upsert `OrgPerson` by `external_id`
3. Reclassify company/electorate/eligibility
4. Soft-deactivate people missing from feed or `is_active=false`

`python manage.py generate_ballot_tokens --year 2026`

- For each `is_nigeria_eligible` and electorate in `{staff, executive}`, create token if missing
- Do not create for Dubai / ineligible roles

---

## Email subsystem (mirror `incel_prospiz`)

Port the same pattern:

1. **`emails/config.py`** — `EmailConfig` reading `EMAIL_ENABLED`, `EMAIL_DEBUG`, `DEFAULT_FROM_EMAIL`, `EMAIL_SENDER_NAME`, etc.
2. **`emails/services/base.py`** — `BaseEmailService.send_email(..., is_async=True)` with daemon thread + `connection.close()` in `finally`
3. **Settings** — console backend in DEBUG; SMTP in production (`smtp-relay.gmail.com` style env vars)
4. **Templates** — `templates/emails/base_email.html` + `vote_invite.html`
5. **Test command** — `test_vote_invite_email --year 2026 --recipient you@incelgroup.com`

### Vote invite content

- Greeting with first name
- Year title + voting open/close times
- Personal ballot CTA button → `{FRONTEND}/{year}/vote?token={token}`
- Short note: link is personal; do not share
- Optional list of award categories they will see (tourism vs global framing)

### Dispatch command

`python manage.py dispatch_vote_invites --year 2026`

Logic:

1. Load `AwardNotificationConfig` for `vote_invite`
2. If disabled → exit
3. If `now < voting_opens_at - offset` → exit (not yet)
4. Resolve audience from config (`all_eligible` for 2026)
5. For each matching token without successful delivery row:
   - Send async or sync-batched email (prefer sync in management command for reliability; or async with join)
   - Write `BallotInviteDelivery`
6. Idempotent: skip tokens already `sent`

**Cron:** every 5–15 minutes around the window. CapRover / system cron calls the command. No Celery required (same philosophy as prospiz).

2026 seed:

```python
AwardNotificationConfig(
  event="vote_invite",
  enabled=True,
  audience="all_eligible",
  offset_minutes_before_open=60,
)
```

---

## Seed command

`python manage.py seed_year_2026`

- Create/update `AwardYear(2026)`
- Create notification config (60 minutes)
- Create all awards, criteria, nominees from a Python seed module `awards/seed/year_2026.py`
- Idempotent (update_or_create by slug)

Keep PDF in repo as reference; seed module is the executable source of truth.

---

## Settings / env checklist

```bash
# Django / DB
DJANGO_DEBUG=
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=
DB_NAME= DB_USER= DB_PASSWORD= DB_HOST= DB_PORT=

# Frontend link generation
FRONTEND_BASE_URL=http://localhost:3000

# Org directory
ORG_USERS_API_BASE_URL=
ORG_USERS_API_TOKEN=

# Email (prospiz-compatible)
EMAIL_BACKEND=
EMAIL_HOST=smtp-relay.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
EMAIL_SENDER_NAME=Incel Group Awards
EMAIL_ENABLED=True
EMAIL_DEBUG=False
```

---

## Test plan (API)

- Classification: Dubai excluded; Tourism exceptions; Global default; ED/MD vs STAFF
- Ballot filtering: Tourism voter never receives Global Employee award
- Vote uniqueness + window enforcement
- Weighted tallies match PDF numeric examples
- Invite dispatch respects offset + idempotency
- Results hidden until published

---

## Implementation notes

- Prefer `select_for_update` on vote upsert to avoid double-submit races
- Never return other voters’ choices on public endpoints
- Log token access sparingly (no full token in logs)
- Admin actions: revoke token, resend invite, publish results, open/close voting
