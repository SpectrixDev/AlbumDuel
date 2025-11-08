from __future__ import annotations

import os
from typing import Optional

import httpx

from .core.config import settings

SPOTIFY_API_BASE = "https://api.spotify.com/v1"


async def fetch_spotify_album_cover(spotify_id: str) -> Optional[str]:
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        return None

    client_id = settings.spotify_client_id
    client_secret = settings.spotify_client_secret

    try:
        async with httpx.AsyncClient() as client:
            auth_resp = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
            )
        if auth_resp.status_code != 200:
            return None
        access_token = auth_resp.json().get("access_token")
        if not access_token:
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SPOTIFY_API_BASE}/albums/{spotify_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            return None

        data = resp.json()
        images = data.get("images") or []
        if images:
            return images[0].get("url")
    except Exception:
        return None

    return None


async def search_spotify_album_cover(title: str, artist: str, year: Optional[int]) -> Optional[str]:
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        return None

    client_id = settings.spotify_client_id
    client_secret = settings.spotify_client_secret

    try:
        async with httpx.AsyncClient() as client:
            auth_resp = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
            )
        if auth_resp.status_code != 200:
            return None
        access_token = auth_resp.json().get("access_token")
        if not access_token:
            return None

        query = f"album:{title} artist:{artist}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SPOTIFY_API_BASE}/search",
                params={"q": query, "type": "album", "limit": 5},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code != 200:
            return None

        data = resp.json()
        items = (data.get("albums") or {}).get("items") or []
        if not items:
            return None

        album = items[0]
        images = album.get("images") or []
        if images:
            return images[0].get("url")
    except Exception:
        return None

    return None
