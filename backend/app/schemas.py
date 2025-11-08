from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .core.elo import elo_to_100


class AlbumBase(BaseModel):
    id: int
    title: str
    artist: str
    year: Optional[int] = None
    cover_url: Optional[str] = None
    spotify_id: Optional[str] = None

    class Config:
        from_attributes = True


class AlbumWithRatings(AlbumBase):
    elo: float
    comparisons_count: int

    @property
    def rating_100(self) -> float:
        return elo_to_100(self.elo)


class ComparePairAlbum(AlbumBase):
    elo: float
    comparisons_count: int


class ComparePair(BaseModel):
    album_a: ComparePairAlbum
    album_b: ComparePairAlbum
    total_comparisons: int


class CompareSubmit(BaseModel):
    album_a_id: int
    album_b_id: int
    winner_album_id: Optional[int] = None


class RankingEntry(BaseModel):
    album: AlbumBase
    elo: float
    rating_100: float
    comparisons_count: int


class RankingsResponse(BaseModel):
    items: list[RankingEntry]


class ExcludeAlbumRequest(BaseModel):
    album_id: int


class StatsResponse(BaseModel):
    total_albums: int
    total_comparisons: int


class UserOut(BaseModel):
    id: int
    display_name: Optional[str]

    class Config:
        from_attributes = True
