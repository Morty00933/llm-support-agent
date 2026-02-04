from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from src.domain.models import User, Ticket, Message
from src.core.security import hash_password

logger = structlog.get_logger(__name__)


class DemoDataSeeder:
    """Seeds database with demo data for showcasing features."""

    @staticmethod
    async def seed_demo_users(session: AsyncSession, tenant_id: int = 1):
        """Create demo users with different roles."""
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.email == "admin@demo.com")
        )
        if result.scalar_one_or_none():
            logger.info("demo_users_already_exist")
            return

        users = [
            {
                "email": "admin@demo.com",
                "hashed_password": hash_password("Admin123"),
                "full_name": "Admin User",
                "role": "admin",
                "is_active": True,
                "tenant_id": tenant_id,
            },
            {
                "email": "user@demo.com",
                "hashed_password": hash_password("User1234"),
                "full_name": "Demo User",
                "role": "user",
                "is_active": True,
                "tenant_id": tenant_id,
            },
            {
                "email": "support@demo.com",
                "hashed_password": hash_password("Support123"),
                "full_name": "Support Agent",
                "role": "agent",
                "is_active": True,
                "tenant_id": tenant_id,
            },
        ]

        for user_data in users:
            user = User(**user_data)
            session.add(user)

        await session.commit()
        logger.info("demo_users_seeded", count=len(users))

    @staticmethod
    async def seed_demo_tickets(session: AsyncSession, tenant_id: int = 1):
        """Create sample tickets with conversation history."""
        # Get first user
        result = await session.execute(
            select(User).where(User.tenant_id == tenant_id).limit(1)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning("no_user_found_for_demo_tickets")
            return

        # Check if demo tickets already exist
        result = await session.execute(
            select(Ticket).where(
                Ticket.tenant_id == tenant_id,
                Ticket.title == "How do I reset my password?"
            ).limit(1)
        )
        if result.scalar_one_or_none():
            logger.info("demo_tickets_already_exist")
            return

        tickets = [
            {
                "title": "How do I reset my password?",
                "description": "I forgot my password and need help resetting it.",
                "status": "resolved",
                "priority": "low",
                "tenant_id": tenant_id,
                "created_by_id": user.id,
                "created_at": datetime.now(timezone.utc) - timedelta(days=2),
            },
            {
                "title": "Unable to create new ticket",
                "description": "Getting error 500 when clicking 'New Ticket' button.",
                "status": "in_progress",
                "priority": "high",
                "tenant_id": tenant_id,
                "created_by_id": user.id,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=5),
            },
            {
                "title": "Question about support hours",
                "description": "What are your operating hours? Do you offer 24/7 support?",
                "status": "open",
                "priority": "medium",
                "tenant_id": tenant_id,
                "created_by_id": user.id,
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=30),
            },
            {
                "title": "Refund request for order #12345",
                "description": "I would like to request a refund for my recent purchase. The product did not meet my expectations.",
                "status": "pending",
                "priority": "medium",
                "tenant_id": tenant_id,
                "created_by_id": user.id,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=12),
            },
            {
                "title": "Account security concern",
                "description": "I noticed unusual activity on my account. Can you help me secure it?",
                "status": "open",
                "priority": "urgent",
                "tenant_id": tenant_id,
                "created_by_id": user.id,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            },
        ]

        for ticket_data in tickets:
            ticket = Ticket(**ticket_data)
            session.add(ticket)
            await session.flush()  # Get ticket ID

            # Add messages
            messages = [
                Message(
                    ticket_id=ticket.id,
                    role="user",
                    content=ticket_data["description"],
                    tenant_id=tenant_id,
                    created_by_id=user.id,
                    created_at=ticket_data["created_at"],
                ),
                Message(
                    ticket_id=ticket.id,
                    role="assistant",
                    content=_get_ai_response_for_ticket(ticket_data["title"]),
                    tenant_id=tenant_id,
                    is_from_agent=True,
                    created_at=ticket_data["created_at"] + timedelta(minutes=2),
                ),
            ]

            for msg in messages:
                session.add(msg)

        await session.commit()
        logger.info("demo_tickets_seeded", count=len(tickets))

    @staticmethod
    async def seed_all(session: AsyncSession, tenant_id: int = 1):
        """Seed all demo data."""
        await DemoDataSeeder.seed_demo_users(session, tenant_id)
        await DemoDataSeeder.seed_demo_tickets(session, tenant_id)
        logger.info("all_demo_data_seeded", tenant_id=tenant_id)


def _get_ai_response_for_ticket(title: str) -> str:
    """Generate AI response based on ticket title."""
    responses = {
        "How do I reset my password?": (
            "Thank you for contacting support! To reset your password:\n\n"
            "1. Click 'Forgot Password' on the login page\n"
            "2. Enter your email address\n"
            "3. Check your email for reset instructions\n"
            "4. Follow the link and create a new password\n\n"
            "If you don't receive the email within 5 minutes, please check your spam folder. "
            "Let me know if you need any further assistance!"
        ),
        "Unable to create new ticket": (
            "I'm sorry to hear you're experiencing issues. Our team is investigating this error. "
            "In the meantime, you can contact us via email at support@example.com. "
            "We'll keep you updated on the progress of this fix."
        ),
        "Question about support hours": (
            "Our support team is available Monday through Friday, 9:00 AM to 6:00 PM EST. "
            "For urgent issues outside business hours, please mark your ticket as 'urgent' "
            "and our on-call team will be notified. We aim to respond to urgent issues within 4 hours."
        ),
        "Refund request for order #12345": (
            "I understand you'd like to request a refund. According to our refund policy, "
            "refund requests must be submitted within 30 days of purchase. "
            "I've created a refund request ticket for you. Please provide:\n\n"
            "1. Order number\n"
            "2. Reason for refund\n"
            "3. Preferred refund method\n\n"
            "Our billing team will review your request within 2-3 business days."
        ),
        "Account security concern": (
            "Thank you for reporting this security concern. I'm escalating this to our security team immediately. "
            "In the meantime, please:\n\n"
            "1. Change your password immediately\n"
            "2. Enable two-factor authentication\n"
            "3. Review recent login activity\n"
            "4. Check for any unauthorized changes\n\n"
            "Our security team will contact you within 1 hour to investigate further."
        ),
    }
    return responses.get(title, "Thank you for contacting support. Our team is reviewing your inquiry and will respond shortly.")
