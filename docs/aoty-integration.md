# Album of the Year (AOTY) Integration

## Overview
The AOTY integration lets authenticated users import albums they have rated on albumoftheyear.org and use them in AlbumDuel duels and leaderboards.

## Backend
- Dependency: `album-of-the-year-api` (imported as `albumoftheyearapi.user.UserMethods`) is installed in the backend virtualenv.
- Entrypoint: `backend/app/aoty_router.py` exposes `POST /import/aoty/user-albums`.
- Handler: `import_aoty_user_albums` in `backend/app/aoty.py`:
  - Uses `UserMethods().user_ratings(aoty_username)` to fetch rated albums.
  - For each rating:
    - Extracts `album`/`album_name`/`title` and `artist`/`artist_name` (skips rows without them).
    - Attempts to find existing `Album` by case-insensitive title+artist.
    - If no match, creates an `Album` with:
      - `source="aoty"`.
      - `cover_url` from the first non-empty of `album_artwork_link`, `cover_url`, `cover`, `image`.
      - Protocol-relative URLs (`//...`) normalized to `https://`.
      - `cover_provider="aoty"` when a cover is set.
    - Calls `resolve_album_cover` to prefer AOTY-provided covers and reuse/augment artwork (Spotify lookup, MBID/Spotify-ID reuse, fuzzy title/artist reuse).
    - Links the album to the current user via `UserAlbum(added_from="aoty")` if not already linked.

## Frontend
- Import UI: `frontend/src/components/AOTYImport.tsx`:
  - Posts `aoty_username` to `/import/aoty/user-albums` and displays imported count or error.
- Usage in views:
  - `/compare/next` includes `cover_url`/`cover_provider` in `ComparePairAlbum`; `Duel.tsx` uses `album.cover_url` for covers with a themed fallback.
  - `/rankings` returns `AlbumBase` objects with `cover_url`/`source`/`cover_provider`; `Leaderboard.tsx` shows a thumbnail using `album.cover_url` when present.

## Notes
- Server must run using the project `.venv` (where `album-of-the-year-api` is installed) so `albumoftheyearapi.user` imports successfully.
- If AOTY responses change their artwork field names, update `backend/app/aoty.py` to map the new keys into `cover_url` and `aoty_cover` selection.
