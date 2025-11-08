# AlbumDuel

AlbumDuel is a web app for ranking albums via head-to-head duels, aggregating data from Spotify, Album of the Year (AOTY), and Last.fm into a single, clean leaderboard per user.

## Features

- Spotify integration:
  - Login with Spotify OAuth.
  - Import top/saved albums.
  - Shared album model to minimize duplicates.
- Album of the Year integration:
  - Import rated albums by AOTY username.
  - Artwork resolution and merging with existing Spotify entries.
- Last.fm integration:
  - Optional scrobble-based imports (when configured).
- Smart deduplication:
  - Backend merges albums by logical identity so AOTY + Spotify versions of the same album are treated as one.
  - Elo and comparisons are combined and leaderboard groups duplicates into a single canonical row.
- Elo-based duels:
  - /compare/next surfaces album pairs.
  - /compare/submit updates per-user Elo.
  - Leaderboard shows ranked albums with covers and exclude controls.
- Stats page:
  - Shows total albums, total duels, and average duels per album with a styled card layout and progress bars toward configurable milestones.

## Tech Stack

- Backend:
  - FastAPI (async)
  - SQLAlchemy async + SQLite (default via `sqlite+aiosqlite`)
  - OAuth / JWT for auth
- Frontend:
  - React + TypeScript
  - Vite dev server

## Setup

### Backend

1. From `backend/`, create `.env` (do NOT commit) based on `backend/.env.example`:
   - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
   - `JWT_SECRET` (set a strong value)
   - `LASTFM_API_KEY`, `LASTFM_API_SECRET` (optional)
   - `DATABASE_URL` (defaults to `sqlite+aiosqlite:///./albumduel.db`)
2. Install dependencies and run:
   - `poetry install`
   - `poetry run uvicorn app.main:app --reload --port 8000`

### Frontend

1. From `frontend/`:
   - `npm install`
   - `npm run dev`
2. Configure the frontend to point at the backend via `API_BASE_URL` if needed.

## Run via helper script

From the repo root:

- `./run.sh`

This starts the backend on `:8000` (Poetry + Uvicorn) and the frontend dev server.

