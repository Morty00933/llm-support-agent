from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.core.config import settings
from src.core.db import get_db
from src.core.demo_data import DemoDataSeeder
from src.api.routers.auth import get_current_active_user
from src.domain.models import User

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["demo"])


@router.post("/seed", summary="Seed demo data")
async def seed_demo_data(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Seed demo data (users, tickets, messages).

    Only available when DEMO_MODE_ENABLED=true.
    """
    if not settings.demo_mode_enabled:
        raise HTTPException(
            status_code=403,
            detail="Demo mode is not enabled. Set DEMO_MODE_ENABLED=true to use this endpoint."
        )

    try:
        await DemoDataSeeder.seed_all(session, tenant_id=current_user.tenant_id)
        logger.info("demo_data_seeded_via_api", tenant_id=current_user.tenant_id)

        return {
            "status": "success",
            "message": "Demo data has been seeded successfully",
            "tenant_id": current_user.tenant_id,
        }
    except Exception as e:
        logger.error("demo_data_seeding_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {str(e)}")


@router.get("/status", summary="Check demo mode status")
async def get_demo_status():
    """Get demo mode configuration status."""
    return {
        "demo_mode_enabled": settings.demo_mode_enabled,
        "demo_seed_on_startup": settings.demo_seed_on_startup,
    }
