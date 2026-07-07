# Trackify

Trackify is a unified media tracking platform — think Goodreads, Letterboxd,
and Last.fm combined into one app, with cross-domain recommendations layered
on top.

A separate recommendation microservice powers the "you liked this, try
that" experience across books, movies, and music using a hybrid
collaborative + content-based approach.

## Status

**Phase 1 (Foundations)** and the **recommendation microservice** are
built.

- **Phase 1** stood up the core app skeleton: the FastAPI backend with
  PostgreSQL + Alembic migrations, JWT-based auth (register, login,
  logout, refresh), and a Vite + React + Tailwind frontend with
  working login/register pages and routing.
- **Recommendation microservice** trains and serves a hybrid
  collaborative + content-based model over books, movies, and music
  metadata, exposed via its own API for cross-domain "you liked this,
  try that" recommendations.

Coming up next: **Phase 2 (Core tracking)** — search across external
media APIs (TMDB, Open Library, MusicBrainz), item detail pages,
library management (add/track status/progress), diary entries, and
reviews, so Trackify works end to end as a standalone tracker.

This repository is under active development.
