from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .aoty import import_aoty_user_albums
from .db import get_db
from .models import User
from .spotify import require_spotify_user

router = APIRouter(prefix="/import/aoty", tags=["aoty"])


class AOTYImportRequest(BaseModel):
    aoty_username: str


@router.post("/user-albums")
async def import_aoty_user_albums_endpoint(
    payload: AOTYImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_spotify_user),
):
    if not payload.aoty_username:
        raise HTTPException(status_code=400, detail="AOTY username is required")

    imported = await import_aoty_user_albums(db, user, payload.aoty_username)

    return {"status": "ok", "imported": imported}
