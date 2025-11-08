from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class SpotifyToken(Base):
    __tablename__ = "spotify_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_provider"),
    )


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, nullable=True, index=True)
    mbid = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    source = Column(String, nullable=True)


class UserAlbum(Base):
    __tablename__ = "user_albums"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    added_from = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_user_album"),
        Index("ix_user_albums_user", "user_id"),
    )


class UserAlbumExclusion(Base):
    __tablename__ = "user_album_exclusions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_user_album_exclusion"),
        Index("ix_user_album_exclusions_user", "user_id"),
    )


class EloScore(Base):
    __tablename__ = "elo_scores"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    elo = Column(Float, default=1500.0)
    comparisons_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_elo_user_album"),
        Index("ix_elo_user", "user_id"),
        Index("ix_elo_elo", "elo"),
    )


class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_a_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    album_b_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    winner_album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_comparisons_user", "user_id"),
    )
