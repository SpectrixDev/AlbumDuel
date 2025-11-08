from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db import get_db
from .models import Album, User, UserAlbum

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/demo-albums")
async def import_demo_albums(db: AsyncSession = Depends(get_db)):
    user_res = await db.execute(select(User).limit(1))
    user = user_res.scalar_one_or_none()
    if not user:
        user = User(provider="demo", provider_user_id="demo", display_name="Demo User")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    demo_albums = [
        {"title": "OK Computer", "artist": "Radiohead"},
        {"title": "To Pimp a Butterfly", "artist": "Kendrick Lamar"},
        {"title": "Kid A", "artist": "Radiohead"},
        {"title": "Random Access Memories", "artist": "Daft Punk"},
    ]

    created = 0
    for da in demo_albums:
        existing_q = await db.execute(
            select(Album).where(Album.title == da["title"], Album.artist == da["artist"])
        )
        album = existing_q.scalar_one_or_none()
        if not album:
            album = Album(title=da["title"], artist=da["artist"], source="demo")
            db.add(album)
            await db.flush()
            created += 1

        link_q = await db.execute(
            select(UserAlbum).where(UserAlbum.user_id == user.id, UserAlbum.album_id == album.id)
        )
        link = link_q.scalar_one_or_none()
        if not link:
            db.add(UserAlbum(user_id=user.id, album_id=album.id, added_from="demo"))

    await db.commit()
    return {"status": "ok", "created_albums": created}
