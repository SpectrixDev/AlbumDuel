from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .models import User
from .spotify import require_spotify_user

router = APIRouter(prefix="/auth", tags=["auth-status"])


@router.get("/status")
async def auth_status(user: User = Depends(require_spotify_user)):
    return {
        "logged_in": True,
        "provider": "spotify",
        "display_name": user.display_name,
    }
