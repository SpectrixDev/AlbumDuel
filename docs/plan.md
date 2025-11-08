# AlbumDuel Plan

This document tracks the evolving architecture, decisions, and implementation plan for the AlbumDuel project.

## High-level goals
- Elo-based album ranking via pairwise comparisons.
- Integrations: Spotify + saved-track album sync, Album of the Year (AOTY) ratings import; Last.fm and MusicBrainz remain optional.
- GitHub Pages-hosted frontend, self-hosted backend.

## Current state
- FastAPI backend with Spotify OAuth login and JWT-based auth.
- Per-user SpotifyToken stored; /import/spotify/top-albums scans /me/tracks with pagination, imports only full-length albums (album_type=album, min 6 tracks), optional max cap.
- /import/aoty/user-albums imports all albums the authenticated user rated on albumoftheyear.org (by provided username), matching existing albums by case-insensitive title/artist or creating AOTY-only records enriched with AOTY artwork when available.
- Cover art strategy (per album): prefer Spotify images; if missing, use AOTY artwork; planned: fall back to Last.fm and MusicBrainz Cover Art Archive; finally use a consistent placeholder.
- Elo compare/submit, rankings, stats now scoped strictly to authenticated Spotify users.
- React+Vite frontend with Duel, Leaderboard, Stats views.
- Header shows Connect Spotify and live auth status with one-click "Refresh" to resync albums.
- Legacy demo import/UI removed.

## Next steps
- Tune sync strategy (configurable top-tracks range and max albums per import) to avoid hitting Spotify rate limits. (Done)
- Add richer analytics and visualizations on top of synced albums.
- Explore Last.fm integration as alternate source.
