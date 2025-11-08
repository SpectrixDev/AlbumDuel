from __future__ import annotations

from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Album


async def resolve_album_cover(
    db: AsyncSession,
    album: Album,
    *,
    aoty_cover_url: Optional[str] = None,
) -> None:
    if album.cover_url:
        return

    if aoty_cover_url:
        album.cover_url = aoty_cover_url
        album.cover_provider = "aoty"
        await db.flush()
        return

    if album.spotify_id:
        from .spotify_resolver import fetch_spotify_album_cover

        cover = await fetch_spotify_album_cover(album.spotify_id)
        if cover:
            album.cover_url = cover
            album.cover_provider = "spotify"
            await db.flush()
            return

    # Try reuse by exact identifiers
    if album.mbid:
        res = await db.execute(
            select(Album.cover_url, Album.cover_provider).where(
                and_(
                    Album.id != album.id,
                    Album.mbid == album.mbid,
                    Album.cover_url.is_not(None),
                )
            )
        )
        row = res.first()
        if row and row[0]:
            album.cover_url = row[0]
            album.cover_provider = row[1] or "copy-mbid"
            await db.flush()
            return

    if album.spotify_id:
        res = await db.execute(
            select(Album.cover_url, Album.cover_provider).where(
                and_(
                    Album.id != album.id,
                    Album.spotify_id == album.spotify_id,
                    Album.cover_url.is_not(None),
                )
            )
        )
        row = res.first()
        if row and row[0]:
            album.cover_url = row[0]
            album.cover_provider = row[1] or "copy-spotify-id"
            await db.flush()
            return

    # Fuzzy-ish reuse: same title/artist (case-insensitive) with any real cover
    res = await db.execute(
        select(Album.cover_url, Album.cover_provider).where(
            and_(
                Album.id != album.id,
                Album.title.ilike(album.title),
                Album.artist.ilike(album.artist),
                Album.cover_url.is_not(None),
            )
        )
    )
    row = res.first()
    if row and row[0]:
        album.cover_url = row[0]
        album.cover_provider = row[1] or "copy-title-artist"
        await db.flush()
        return

    # Last resort: try fetching from Spotify search using title/artist/year
    from .spotify_resolver import search_spotify_album_cover

    cover = await search_spotify_album_cover(album.title, album.artist, album.year)
    if cover:
        album.cover_url = cover
        album.cover_provider = "spotify-search"
        await db.flush()


__all__ = ["resolve_album_cover"]
