from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Album, User, UserAlbum

try:
    from albumoftheyearapi.user import UserMethods  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    UserMethods = None  # type: ignore


async def import_aoty_user_albums(
    db: AsyncSession,
    user: User,
    aoty_username: str,
) -> int:
    if UserMethods is None:
        raise RuntimeError("Album of the Year integration is not available on this server.")

    client = UserMethods()

    try:
        rated_albums = client.user_ratings(aoty_username)
    except Exception as exc:  # pragma: no cover - upstream/network issues
        raise RuntimeError(f"Failed to fetch AOTY data: {exc}")

    imported = 0

    for item in rated_albums:
        title = (item.get("album") or item.get("album_name") or item.get("title") or "").strip()
        artist = (item.get("artist") or item.get("artist_name") or "").strip()
        year: Optional[int] = None
        try:
            raw_year = item.get("year") or item.get("release_year")
            if raw_year:
                year = int(str(raw_year))
        except (TypeError, ValueError):
            year = None

        if not title or not artist:
            continue

        res = await db.execute(
            select(Album).where(
                Album.title.ilike(title),
                Album.artist.ilike(artist),
            )
        )
        album = res.scalars().first()

        if album and album.spotify_id:
            continue

        if not album:
            cover_url = item.get("album_artwork_link") or item.get("cover") or item.get("image")

            album = Album(
                title=title,
                artist=artist,
                year=year,
                cover_url=cover_url,
                source="aoty",
            )
            db.add(album)
            await db.flush()

        link_res = await db.execute(
            select(UserAlbum).where(
                UserAlbum.user_id == user.id,
                UserAlbum.album_id == album.id,
            )
        )
        link = link_res.scalar_one_or_none()
        if not link:
            db.add(
                UserAlbum(
                    user_id=user.id,
                    album_id=album.id,
                    added_from="aoty",
                )
            )
            imported += 1

    await db.commit()
    return imported
