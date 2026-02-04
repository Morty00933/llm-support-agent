#!/usr/bin/env python3
"""
Seed demo users for LLM Support Agent

Usage:
    python scripts/seed_demo_users.py

Or via Docker:
    docker-compose exec backend python scripts/seed_demo_users.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.core.demo_data import DemoDataSeeder
import structlog

logger = structlog.get_logger(__name__)


async def main():
    """Seed demo users and tickets."""

    # Create async engine
    engine = create_async_engine(
        settings.database.async_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("Starting demo data seeding...")

    try:
        async with async_session() as session:
            # Seed users
            logger.info("Seeding demo users...")
            await DemoDataSeeder.seed_demo_users(session, tenant_id=1)

            # Seed tickets
            logger.info("Seeding demo tickets...")
            await DemoDataSeeder.seed_demo_tickets(session, tenant_id=1)

        logger.info("Demo data seeding completed successfully!")
        logger.info("")
        logger.info("Demo accounts created:")
        logger.info("  Admin:   admin@demo.com   / admin123")
        logger.info("  User:    user@demo.com    / user123")
        logger.info("  Support: support@demo.com / support123")

    except Exception as e:
        logger.error("Failed to seed demo data", error=str(e))
        raise

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
