# Incel Awards — Frontend

Next.js (App Router) public site for Incel Group Employee Awards.

Talks to the Django API at `NEXT_PUBLIC_API_BASE_URL` (local default: `http://localhost:8000/api/v1`).

## Setup

```bash
cd frontend
cp .env.example .env.local   # already points at localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Run the API first:

```bash
cd api
source venv/bin/activate
python manage.py runserver 8000
```

Ballot links: `/{year}/vote?token=<token>` from `generate_ballot_tokens` / invite email.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Local development |
| `npm run build` | Production build |
| `npm run start` | Serve production build |
| `npm run lint` | ESLint |

## Routes

| Path | Purpose |
|---|---|
| `/` | Home / overview |
| `/[year]` | Year hub |
| `/[year]/awards` | Award catalogue |
| `/[year]/awards/[slug]` | Award detail |
| `/[year]/vote?token=` | Ballot (token required) |
| `/[year]/results` | Published results |

## Design

Visual system is documented at the repo root in `DESIGN.md` / `.impeccable/design.json` — ceremonial woven-textile world (indigo / gold / teal).
