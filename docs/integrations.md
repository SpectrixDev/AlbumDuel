# Integrations Overview

This document summarizes how AlbumDuel integrates with external services and how imported data flows into duels, rankings, and stats.

## Spotify
- Auth: Implemented via FastAPI router in `backend/app/spotify.py` with OAuth and per-user `SpotifyToken` records.
- Import:
  - `POST /import/spotify/top-albums` scans the user's saved tracks via Spotify Web API.
  - Only includes full-length albums (e.g., `album_type == "album"`, minimum track thresholds) to avoid clutter.
  - Creates or updates `Album` rows with `spotify_id`, metadata, and cover art from Spotify images.
  - Links albums to the user via `UserAlbum(added_from="spotify")`.
- Usage:
  - `/compare/next`, `/rankings`, and `/stats` all operate on the user's imported Spotify albums (filtered by exclusions).

## Album of the Year (AOTY)
- See `docs/aoty-integration.md` for full details.
- High level:
  - `POST /import/aoty/user-albums` fetches rated albums for a provided AOTY username using `albumoftheyearapi.user.UserMethods`.
  - Creates/links `Album` + `UserAlbum` entries and populates `cover_url` from AOTY artwork fields with normalization.
  - Artwork is reused or enhanced by `resolve_album_cover`.

## Last.fm
- Auth and import implemented in `backend/app/lastfm.py`.
- Login flow:
  - Redirects to Last.fm OAuth-like page; on callback, exchanges for a session key.
  - Keeps session data in-memory (`LASTFM_SESSIONS`) keyed by AlbumDuel user id.
- Import:
  - `POST /import/lastfm/top-albums` uses `user.getTopAlbums`.
  - For each entry, `_find_or_create_album` either reuses or creates an `Album` with Last.fm image/MBID, setting `source="lastfm"` when appropriate.
  - Albums are linked via `UserAlbum(added_from="lastfm")`.

## Artwork Resolution
- Centralized in `backend/app/artwork_resolver.py`:
  - Short-circuits if `Album.cover_url` already set.
  - Uses AOTY cover when provided.
  - Falls back to:
    - Direct Spotify cover by `spotify_id`.
    - Reusing cover from another album row with same MBID or Spotify ID.
    - Reusing cover by matching title+artist.
    - Spotify search by title/artist/year.
- Ensures a consistent, best-effort cover for all albums, minimizing duplicate lookups.

## How This Feeds The UI
- Duel (`frontend/src/components/Duel.tsx`):
  - Requests `/compare/next` which returns two `ComparePairAlbum`s, each carrying `cover_url` and metadata.
  - Renders real covers when present; otherwise uses a dark-themed placeholder.
- Leaderboard (`frontend/src/components/Leaderboard.tsx`):
  - Uses `/rankings` to show per-album Elo, rating/100, source, cover provider, and a thumbnail from `cover_url`.
- Stats (`frontend/src/components/Stats.tsx`):
  - Uses `/stats` to summarize total albums and comparisons based on all integrated sources.
