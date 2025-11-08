from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db import get_db
from .models import Album, User, UserAlbum
from .spotify import require_spotify_user

router = APIRouter(prefix="/auth/lastfm", tags=["lastfm"])
import_router = APIRouter(prefix="/import/lastfm", tags=["lastfm-import"])

LASTFM_AUTH_URL = "https://www.last.fm/api/auth/"
LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"


def _get_lastfm_creds() -> tuple[str, str]:
    api_key = settings.lastfm_api_key
    api_secret = settings.lastfm_api_secret
    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="Last.fm is not configured on this server.")
    return api_key, api_secret


def _sign_lastfm(params: Dict[str, Any], api_secret: str) -> str:
    # Last.fm signature: concat all params (except format) sorted by key + secret, md5
    items = [f"{k}{v}" for k, v in sorted(params.items()) if k != "format"]
    raw = "".join(items) + api_secret
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@router.get("/login")
async def lastfm_login():
    api_key, _ = _get_lastfm_creds()
    cb = os.getenv("LASTFM_REDIRECT_URI", f"{settings.api_base_url}/auth/lastfm/callback")
    return RedirectResponse(url=f"{LASTFM_AUTH_URL}?api_key={api_key}&cb={cb}")


@router.get("/callback")
async def lastfm_callback(token: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_spotify_user)):
    api_key, api_secret = _get_lastfm_creds()
    params = {
        "method": "auth.getSession",
        "api_key": api_key,
        "token": token,
        "format": "json",
    }
    sig = _sign_lastfm(params, api_secret)
    params["api_sig"] = sig

    async with httpx.AsyncClient() as client:
        r = await client.get(LASTFM_API_URL, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Last.fm auth failed")

    data = r.json()
    if "session" not in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Last.fm response")

    session = data["session"]
    username = session.get("name")
    key = session.get("key")
    if not username or not key:
        raise HTTPException(status_code=400, detail="Missing Last.fm session data")

    # Store in-memory mapping for now; could be persisted if needed.
    # We keep it simple to avoid schema migration.
    # Keyed by user.id for import endpoints.
    LASTFM_SESSIONS[user.id] = {"username": username, "key": key}

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173/AlbumDuel")
    return RedirectResponse(url=f"{frontend_url}/auth/lastfm/callback?linked=1")


LASTFM_SESSIONS: Dict[int, Dict[str, str]] = {}


def _normalize(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace()).strip()


async def _find_or_create_album(
    db: AsyncSession,
    *,
    artist: str,
    title: str,
    mbid: Optional[str],
    image_url: Optional[str],
    source_hint: str,
) -> Album:
    norm_artist = _normalize(artist)
    norm_title = _normalize(title)

    if mbid:
        res = await db.execute(select(Album).where(Album.mbid == mbid))
        album = res.scalar_one_or_none()
        if album:
            if not album.cover_url and image_url:
                album.cover_url = image_url
                album.cover_provider = source_hint
            if not album.source:
                album.source = source_hint
            return album

    res = await db.execute(
        select(Album).where(
            _normalize(Album.artist) == norm_artist,
            _normalize(Album.title) == norm_title,
        )
    )
    album = res.scalar_one_or_none()
    if album:
        if not album.cover_url and image_url:
            album.cover_url = image_url
            album.cover_provider = source_hint
        if album.source != "spotify":
            album.source = "spotify" if album.spotify_id else (album.source or source_hint)
        return album

    album = Album(
        artist=artist,
        title=title,
        cover_url=image_url,
        source=source_hint,
        cover_provider=source_hint,
        mbid=mbid,
    )
    db.add(album)
    await db.flush()
    return album


async def _lastfm_api_get(user_key: str, extra_params: Dict[str, Any]) -> Dict[str, Any]:
    api_key, _ = _get_lastfm_creds()
    params = {
        "api_key": api_key,
        "sk": user_key,
        "format": "json",
    }
    params.update(extra_params)
    async with httpx.AsyncClient() as client:
        r = await client.get(LASTFM_API_URL, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Last.fm API error: {r.text}")
    return r.json()


@import_router.post("/top-albums")
async def import_lastfm_top_albums(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_spotify_user),
    limit: int = 200,
):
    sess = LASTFM_SESSIONS.get(user.id)
    if not sess:
        raise HTTPException(status_code=400, detail="Last.fm not linked for this user")

    username = sess["username"]
    key = sess["key"]

    limit = max(10, min(limit, 500))

    data = await _lastfm_api_get(key, {"method": "user.getTopAlbums", "user": username, "limit": limit})
    albums = data.get("topalbums", {}).get("album", [])

    imported = 0
    for a in albums:
        name = a.get("name")
        artist = a.get("artist", {}).get("name") or ""
        if not name or not artist:
            continue
        mbid = a.get("mbid") or None
        imgs = a.get("image") or []
        image_url = imgs[-1]["#text"] if imgs else None

        album = await _find_or_create_album(
            db,
            artist=artist,
            title=name,
            mbid=mbid,
            image_url=image_url,
            source_hint="lastfm",
        )

        res = await db.execute(
            select(UserAlbum).where(UserAlbum.user_id == user.id, UserAlbum.album_id == album.id)
        )
        link = res.scalar_one_or_none()
        if not link:
            db.add(UserAlbum(user_id=user.id, album_id=album.id, added_from="lastfm"))
            imported += 1

    await db.commit()
    return {"status": "ok", "imported": imported}
