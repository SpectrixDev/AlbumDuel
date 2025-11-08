from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .core.elo import update_elo, elo_to_100
from .db import get_db, init_db
from .models import Album, EloScore, Comparison, User, UserAlbumExclusion
from .schemas import ComparePair, ComparePairAlbum, CompareSubmit, RankingsResponse, RankingEntry, StatsResponse, ExcludeAlbumRequest
from .auth import router as auth_router
from .imports import router as import_router
from .spotify import router as spotify_auth_router, import_router as spotify_import_router, require_spotify_user


def choose_canonical_album(a: Album, b: Album) -> Album:
    # Prefer album with spotify_id, else with any cover_url, else newer year, else higher id for stability.
    if bool(a.spotify_id) != bool(b.spotify_id):
        return a if a.spotify_id else b
    if bool(a.cover_url) != bool(b.cover_url):
        return a if a.cover_url else b
    if (a.year or 0) != (b.year or 0):
        return a if (a.year or 0) >= (b.year or 0) else b
    return a if a.id >= b.id else b
from .aoty_router import router as aoty_import_router
from .lastfm import router as lastfm_router, import_router as lastfm_import_router
from .auth_status import router as auth_status_router


app = FastAPI(title="AlbumDuel API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    
    
app.include_router(auth_router)
app.include_router(import_router)
app.include_router(spotify_auth_router)
app.include_router(spotify_import_router)
app.include_router(auth_status_router)
app.include_router(aoty_import_router)
app.include_router(lastfm_router)
app.include_router(lastfm_import_router)


async def get_current_user_id(user = Depends(require_spotify_user)) -> int:
    return user.id


@app.get("/compare/next", response_model=ComparePair)
async def get_next_pair(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Simple random pair from user's albums (or global fallback)
    res = await db.execute(
        select(Album)
        .where(~Album.id.in_(
            select(UserAlbumExclusion.album_id).where(UserAlbumExclusion.user_id == user_id)
        ))
        .order_by(func.random())
        .limit(2)
    )
    albums = res.scalars().all()
    if len(albums) < 2:
        raise HTTPException(status_code=400, detail="Not enough albums to compare")

    pairs = []
    for a in albums:
        elo_row = await db.execute(
            select(EloScore).where(EloScore.user_id == user_id, EloScore.album_id == a.id)
        )
        elo = elo_row.scalar_one_or_none()
        pairs.append(
            ComparePairAlbum(
                id=a.id,
                title=a.title,
                artist=a.artist,
                year=a.year,
                cover_url=a.cover_url,
                spotify_id=a.spotify_id,
                source=a.source,
                cover_provider=a.cover_provider,
                elo=elo.elo if elo else 1500.0,
                comparisons_count=elo.comparisons_count if elo else 0,
            )
        )

    total_comparisons_res = await db.execute(
        select(func.count()).select_from(Comparison).where(Comparison.user_id == user_id)
    )

    return ComparePair(album_a=pairs[0], album_b=pairs[1], total_comparisons=total_comparisons_res.scalar_one())


@app.post("/compare/submit")
async def submit_comparison(
    payload: CompareSubmit,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if payload.album_a_id == payload.album_b_id:
        raise HTTPException(status_code=400, detail="Albums must be different")

    res = await db.execute(select(Album).where(Album.id.in_([payload.album_a_id, payload.album_b_id])))
    albums = {a.id: a for a in res.scalars().all()}
    if len(albums) != 2:
        raise HTTPException(status_code=404, detail="Albums not found")

    res = await db.execute(
        select(EloScore).where(
            EloScore.user_id == user_id, EloScore.album_id.in_([payload.album_a_id, payload.album_b_id])
        )
    )
    elo_rows = {e.album_id: e for e in res.scalars().all()}

    def ensure_elo(album_id: int) -> EloScore:
        if album_id not in elo_rows:
            es = EloScore(user_id=user_id, album_id=album_id, elo=1500.0, comparisons_count=0)
            db.add(es)
            elo_rows[album_id] = es
        return elo_rows[album_id]

    ea = ensure_elo(payload.album_a_id)
    eb = ensure_elo(payload.album_b_id)

    if payload.winner_album_id is None:
        score_a = 0.5
    elif payload.winner_album_id == payload.album_a_id:
        score_a = 1.0
    elif payload.winner_album_id == payload.album_b_id:
        score_a = 0.0
    else:
        raise HTTPException(status_code=400, detail="winner_album_id must be one of the compared albums or null")

    new_a, new_b = update_elo(ea.elo, eb.elo, score_a, ea.comparisons_count, eb.comparisons_count)
    ea.elo, eb.elo = new_a, new_b
    ea.comparisons_count += 1
    eb.comparisons_count += 1

    cmp_row = Comparison(
        user_id=user_id,
        album_a_id=payload.album_a_id,
        album_b_id=payload.album_b_id,
        winner_album_id=payload.winner_album_id,
    )
    db.add(cmp_row)
    await db.commit()

    return {"status": "ok"}


@app.post("/albums/exclude")
async def exclude_album(payload: ExcludeAlbumRequest, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    existing = await db.execute(
        select(UserAlbumExclusion).where(
            UserAlbumExclusion.user_id == user_id,
            UserAlbumExclusion.album_id == payload.album_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(UserAlbumExclusion(user_id=user_id, album_id=payload.album_id))
        await db.commit()
    return {"status": "ok"}


@app.get("/rankings", response_model=RankingsResponse)
async def get_rankings(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Aggregate by logical album (title/artist/year), prefer canonical with artwork/source icon, merge Elo within group.
    res = await db.execute(
        select(Album, EloScore)
        .join(EloScore, (EloScore.album_id == Album.id) & (EloScore.user_id == user_id))
        .where(~Album.id.in_(
            select(UserAlbumExclusion.album_id).where(UserAlbumExclusion.user_id == user_id)
        ))
    )
    rows = [(album, elo) for album, elo in res.all()]

    groups: dict[tuple[str, str], list[tuple[Album, EloScore]]] = {}
    for album, elo in rows:
        key = (album.title.strip().lower(), album.artist.strip().lower())
        existing = groups.get(key)
        if existing and any(a.id == album.id for a, _ in existing):
            continue
        groups.setdefault(key, []).append((album, elo))

    items: list[RankingEntry] = []

    for key, entries in groups.items():
        # Merge Elo within this logical album group.
        total_weighted_elo = 0.0
        total_weight = 0
        total_comparisons = 0
        canonical = None

        for album, elo in entries:
            weight = max(1, elo.comparisons_count)
            total_weighted_elo += elo.elo * weight
            total_weight += weight
            total_comparisons += elo.comparisons_count

            if canonical is None:
                canonical = album
            else:
                canonical = choose_canonical_album(canonical, album)

        merged_elo = total_weighted_elo / total_weight if total_weight > 0 else 1500.0
        rating = elo_to_100(merged_elo)

        items.append(
            RankingEntry(
                album=canonical,
                elo=merged_elo,
                rating_100=rating,
                comparisons_count=total_comparisons,
            )
        )

    items.sort(key=lambda x: x.elo, reverse=True)
    return RankingsResponse(items=items)


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    albums_res = await db.execute(
        select(func.count()).select_from(EloScore).where(
            EloScore.user_id == user_id,
            ~EloScore.album_id.in_(
                select(UserAlbumExclusion.album_id).where(UserAlbumExclusion.user_id == user_id)
            ),
        )
    )
    comps_res = await db.execute(
        select(func.count()).select_from(Comparison).where(
            Comparison.user_id == user_id,
            ~Comparison.album_a_id.in_(
                select(UserAlbumExclusion.album_id).where(UserAlbumExclusion.user_id == user_id)
            ),
            ~Comparison.album_b_id.in_(
                select(UserAlbumExclusion.album_id).where(UserAlbumExclusion.user_id == user_id)
            ),
        )
    )
    return StatsResponse(total_albums=albums_res.scalar_one(), total_comparisons=comps_res.scalar_one())
