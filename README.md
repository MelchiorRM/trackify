# Trackify

Trackify is a unified media tracking platform — think Goodreads, Letterboxd,
and Last.fm combined into one app, with cross-domain recommendations layered
on top.

A separate recommendation microservice powers the "you liked this, try
that" experience across books, movies, and music using a hybrid
collaborative + content-based approach.

## Status

**Phase 1 (Foundations)**, **Phase 2 (Core tracking)**, and the
**recommendation microservice** are built.

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
- **Recommendation microservice** trains and serves a hybrid
  collaborative + content-based model over books, movies, and music
  metadata, exposed via its own API for cross-domain "you liked this,
  try that" recommendations.

This repository is under active development.
