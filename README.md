# Trackify

A unified media tracking platform — one web app for books, movies, and
music, combining Goodreads-style book tracking, Letterboxd-style movie
logging, and Last.fm-style listening history in a single account. Search
external catalogs, track status/progress, keep a diary of sessions
(rewatches included), write star ratings and reviews, follow other users
and interact with their activity (likes, comments, reposts, posts, DMs),
and get cross-domain recommendations ("you liked this movie, try this
book") from a companion hybrid recommendation microservice.

## Project layout

```
Trackify/
  trackify-app/
    backend/    FastAPI + SQLAlchemy (async) + Alembic + JWT auth
    frontend/   Vite + React + Tailwind + shadcn-style components
    e2e/        Real-browser checkpoint tests (Playwright)
  recommendation/
    api/        FastAPI serving layer for the recommendation microservice
    pipepline/  Data fetch/preprocess/embed scripts
    training/   ALS + LightGBM hybrid ranker training
  scripts/
    local-services.sh   Start/stop a local Postgres + Redis without Docker
  docker-compose.yml     postgres + redis + backend + frontend
```

The web app and the recommendation service are separate deployables that
share one PostgreSQL instance once the rec service's DB integration
lands. Each has its own `requirements.txt`.

## Getting started

### Prerequisites

- Python 3.12+
- Node 20+ / npm
- PostgreSQL 16 and Redis (via Docker, your own install, or
  `scripts/local-services.sh` for a no-Docker local setup)

### Backend

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r trackify-app/backend/requirements.txt
cp trackify-app/backend/.env.example trackify-app/backend/.env   # fill in DATABASE_URL/REDIS_URL/SECRET_KEY
cd trackify-app/backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If you're using `scripts/local-services.sh` instead of Docker for
Postgres/Redis, note it binds them on non-default ports (5433 and 6380)
to avoid colliding with any system-wide install — adjust `DATABASE_URL`/
`REDIS_URL` in `.env` accordingly.

### Frontend

```bash
cd trackify-app/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Recommendation service

```bash
source venv/bin/activate
pip install -r recommendation/requirements.txt
cd recommendation
uvicorn api.main:app --reload --port 8001
```

Needs a `recommendation/.env` with `TMDB_TOKEN` (or `TMBD_KEY`) for the
TMDB enrichment step (`pipepline/enrich_tmdb.py`) — the only external API
key the pipeline actually reads. Books use goodbooks-10k's own tags
(no Open Library key needed) and music uses a manually-placed Spotify
track-features CSV, not the Spotify API, so no book/music API keys are
required despite earlier plans considering them.

The backend's `/recommendations` and `/discover` endpoints call this
service over HTTP (`REC_SERVICE_URL` in `trackify-app/backend/.env`,
defaults to `http://localhost:8001`) and degrade to a local popularity
query if it's unreachable — it isn't required for the rest of the app to
run.

### Tests

```bash
# Backend unit tests (SQLite/fakeredis substitutes, no services needed)
cd trackify-app/backend && source ../../venv/bin/activate
python -m pytest

# Real-browser checkpoints (needs backend + frontend + Postgres + Redis running)
cd trackify-app && source ../venv/bin/activate
python3 e2e/test_phase1_auth.py
python3 e2e/test_phase2_core_tracking.py
python3 e2e/test_phase3_stats_identity.py
python3 e2e/test_phase4_social.py
```

## Status

**Phase 1 (Foundations)**, **Phase 2 (Core tracking)**, **Phase 3
(Stats & personal identity)**, **Phase 4 (Social graph & interaction)**,
and the **recommendation microservice** are built.

- **Phase 1** stood up the core app skeleton: the FastAPI backend with
  PostgreSQL + Alembic migrations, JWT-based auth (register, login,
  logout, refresh), and a Vite + React + Tailwind frontend with
  working login/register pages and routing.
- **Phase 2** rounds Trackify out into a standalone tracker end to
  end: search across external media APIs (TMDB, Open Library,
  MusicBrainz), item detail pages, library management (add/track
  status/progress), diary entries (including auto-logged entries on
  completion and explicit rewatches), and star ratings + reviews.
  Covered by a real-browser Playwright checkpoint
  (`trackify-app/e2e/test_phase2_core_tracking.py`) alongside the
  backend test suite.
- **Phase 3** builds personal identity and reflection on top of the
  tracker: a stats dashboard (per-domain totals, ratings distribution,
  top genres, monthly consumption, completion rate, longest streak),
  up to 4 cross-domain pinned favorites, a public profile page
  (library, reviews, collections, and paginated diary for any
  username), and collections (shareable, ordered lists of items).
  Covered by a real-browser Playwright checkpoint
  (`trackify-app/e2e/test_phase3_stats_identity.py`) alongside the
  backend test suite.
- **Phase 4** adds the social graph: follows, likes and reposts (on
  reviews and posts), comments with @mention parsing, a notifications
  system (follow/like/comment/mention/repost triggers, unread badge,
  mark-read), and a cursor-paginated activity feed merging all of the
  above from followed users. Beyond appPlan.txt's original Phase 4
  scope, it also ships a lightweight post type (a free-text update not
  tied to a tracked item — commentable and likeable like a review) and
  direct messages between users (conversations, unread counts) — both
  originally listed under "what this plan does not cover" but built
  alongside the rest of Phase 4. Covered by a real-browser Playwright
  checkpoint (`trackify-app/e2e/test_phase4_social.py`, two accounts
  across two browser contexts) alongside the backend test suite.
- **Recommendation microservice** trains and serves a hybrid
  collaborative + content-based model over books, movies, and music
  metadata, exposed via its own API for cross-domain "you liked this,
  try that" recommendations.

This repository is under active development.
