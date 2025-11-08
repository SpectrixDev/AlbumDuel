from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db import engine as async_engine
from .models import Album, EloScore, UserAlbum, Comparison
from .main import choose_canonical_album


async def merge_duplicates() -> None:
    async with AsyncSession(async_engine) as db:
        res = await db.execute(select(Album))
        albums: List[Album] = list(res.scalars().all())

        groups: Dict[Tuple[str, str, int | None], List[Album]] = defaultdict(list)
        for a in albums:
            key = (a.title.strip().lower(), a.artist.strip().lower(), a.year)
            groups[key].append(a)

        for key, alist in groups.items():
            if len(alist) < 2:
                continue

            canonical = alist[0]
            for a in alist[1:]:
                canonical = choose_canonical_album(canonical, a)

            others = [a for a in alist if a.id != canonical.id]
            if not others:
                continue

            for dup in others:
                # Merge EloScore per (user, canonical)
                res = await db.execute(select(EloScore).where(EloScore.album_id == dup.id))
                dup_elos = list(res.scalars().all())
                for de in dup_elos:
                    existing_q = await db.execute(
                        select(EloScore).where(
                            EloScore.user_id == de.user_id,
                            EloScore.album_id == canonical.id,
                        )
                    )
                    existing = existing_q.scalar_one_or_none()
                    if existing:
                        total_cc = existing.comparisons_count + de.comparisons_count
                        if total_cc > 0:
                            existing.elo = (
                                existing.elo * existing.comparisons_count
                                + de.elo * de.comparisons_count
                            ) / total_cc
                        existing.comparisons_count = total_cc
                        await db.delete(de)
                    else:
                        de.album_id = canonical.id

                # Repoint UserAlbum
                res = await db.execute(select(UserAlbum).where(UserAlbum.album_id == dup.id))
                for ua in res.scalars().all():
                    existing_q = await db.execute(
                        select(UserAlbum).where(
                            UserAlbum.user_id == ua.user_id,
                            UserAlbum.album_id == canonical.id,
                        )
                    )
                    if existing_q.scalar_one_or_none():
                        await db.delete(ua)
                    else:
                        ua.album_id = canonical.id

                # Repoint Comparison
                res = await db.execute(
                    select(Comparison).where(
                        (Comparison.album_a_id == dup.id)
                        | (Comparison.album_b_id == dup.id)
                        | (Comparison.winner_album_id == dup.id)
                    )
                )
                for c in res.scalars().all():
                    if c.album_a_id == dup.id:
                        c.album_a_id = canonical.id
                    if c.album_b_id == dup.id:
                        c.album_b_id = canonical.id
                    if c.winner_album_id == dup.id:
                        c.winner_album_id = canonical.id
                    if c.album_a_id == c.album_b_id:
                        # Invalid self-comparison; drop it.
                        await db.delete(c)

                await db.delete(dup)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(merge_duplicates())
