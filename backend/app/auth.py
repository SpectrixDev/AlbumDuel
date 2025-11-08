from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db import get_db
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).limit(1))
    existing = user.scalar_one_or_none()
    if not existing:
        demo = User(provider="demo", provider_user_id="demo", display_name="Demo User")
        db.add(demo)
        await db.commit()
        await db.refresh(demo)
        existing = demo
    return {"id": existing.id, "display_name": existing.display_name or "User"}
