from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db import get_db
from .models import User, Album, UserAlbum, SpotifyToken
from .aoty import import_aoty_user_albums
import jwt

router = APIRouter(prefix="/auth/spotify", tags=["spotify"])

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SCOPES = "user-library-read playlist-read-private user-top-read"


async def get_spotify_client():
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise HTTPException(status_code=500, detail="Spotify is not configured on this server.")


@router.get("/login")
async def spotify_login():
    await get_spotify_client()
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", f"{settings.api_base_url}/auth/spotify/callback")
    params = {
        "response_type": "code",
        "client_id": settings.spotify_client_id,
        "scope": SCOPES,
        "redirect_uri": redirect_uri,
    }
    query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
    return RedirectResponse(url=f"{SPOTIFY_AUTH_URL}?{query}")


@router.get("/callback")
async def spotify_callback(code: str, db: AsyncSession = Depends(get_db)):
    await get_spotify_client()
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", f"{settings.api_base_url}/auth/spotify/callback")

    auth = (settings.spotify_client_id, settings.spotify_client_secret)  # type: ignore[arg-type]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(SPOTIFY_TOKEN_URL, data=data, auth=auth)
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Spotify auth failed")

    token_data = resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    async with httpx.AsyncClient() as client:
        me_resp = await client.get(
            f"{SPOTIFY_API_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if me_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Spotify profile")
    me = me_resp.json()

    spotify_user_id = me["id"]
    display_name = me.get("display_name") or me.get("id")

    res = await db.execute(
        select(User).where(User.provider == "spotify", User.provider_user_id == spotify_user_id)
    )
    user = res.scalar_one_or_none()
    if not user:
        user = User(provider="spotify", provider_user_id=spotify_user_id, display_name=display_name)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    expires_at = int(time.time()) + int(expires_in)

    token_res = await db.execute(select(SpotifyToken).where(SpotifyToken.user_id == user.id))
    st = token_res.scalar_one_or_none()
    if not st:
        st = SpotifyToken(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.add(st)
    else:
        st.access_token = access_token
        if refresh_token:
            st.refresh_token = refresh_token
        st.expires_at = expires_at

    await db.commit()

    session_token = jwt.encode({"sub": str(user.id), "provider": "spotify"}, settings.jwt_secret, algorithm="HS256")

    # Redirect back to frontend with token so SPA can store it
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173/AlbumDuel")
    return RedirectResponse(url=f"{frontend_url}/auth/spotify/callback?token={session_token}")


from fastapi import Header


async def require_spotify_user(
    db: AsyncSession = Depends(get_db), authorization: str | None = Header(default=None)
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub"))
    res = await db.execute(select(User).where(User.id == user_id, User.provider == "spotify"))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


import_router = APIRouter(prefix="/import/spotify", tags=["spotify-import"])


async def _spotify_get(access_token: str, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_API_BASE}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Spotify API error: {r.text}")
    return r.json()


MIN_TRACKS_FOR_ALBUM = 6


async def _upsert_album_from_spotify(db: AsyncSession, user: User, item: Dict[str, Any]) -> None:
    album = item["album"] if "album" in item else item

    album_type = (album.get("album_type") or "").lower()
    if album_type != "album":
        return

    total_tracks = album.get("total_tracks") or 0
    if total_tracks and total_tracks < MIN_TRACKS_FOR_ALBUM:
        return

    spotify_id = album["id"]
    title = album["name"]
    artist = ", ".join(a["name"] for a in album.get("artists", []))
    year = int(album["release_date"][:4]) if album.get("release_date") else None
    cover_url = None
    images = album.get("images") or []
    if images:
        cover_url = images[0]["url"]

    res = await db.execute(select(Album).where(Album.spotify_id == spotify_id))
    existing = res.scalar_one_or_none()
    if not existing:
        existing = Album(
            spotify_id=spotify_id,
            title=title,
            artist=artist,
            year=year,
            cover_url=cover_url,
            source="spotify",
        )
        db.add(existing)
        await db.flush()

    link_res = await db.execute(
        select(UserAlbum).where(UserAlbum.user_id == user.id, UserAlbum.album_id == existing.id)
    )
    link = link_res.scalar_one_or_none()
    if not link:
        db.add(UserAlbum(user_id=user.id, album_id=existing.id, added_from="spotify"))


@import_router.post("/top-albums")
async def import_top_albums(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_spotify_user),
    max_albums: int | None = None,
):
    token_res = await db.execute(select(SpotifyToken).where(SpotifyToken.user_id == user.id))
    st = token_res.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=400, detail="No Spotify token; reconnect.")

    if st.expires_at <= int(time.time()) and not st.refresh_token:
        raise HTTPException(status_code=400, detail="Spotify token expired and no refresh token available.")

    cap = None
    if max_albums is not None:
        cap = max(10, min(max_albums, 2000))

    imported = 0
    limit = 50
    offset = 0

    while True:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SPOTIFY_API_BASE}/me/tracks",
                headers={"Authorization": f"Bearer {st.access_token}"},
                params={"limit": limit, "offset": offset},
            )

        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", "1"))
            await httpx.AsyncClient().aclose()
            time.sleep(min(retry_after, 5))
            continue

        if r.status_code != 200:
            break

        data = r.json()
        items = data.get("items", [])
        if not items:
            break

        for wrapper in items:
            if cap is not None and imported >= cap:
                break
            track = wrapper.get("track") or {}
            if not track:
                continue
            await _upsert_album_from_spotify(db, user, track)
            imported += 1

        if len(items) < limit or (cap is not None and imported >= cap):
            break

        offset += limit

    await db.commit()
    return {"status": "ok", "imported": imported, "source": "saved_tracks", "max_albums": cap}
