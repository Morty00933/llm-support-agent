"""Initial bootstrap migration with required extensions and core tables."""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision: str = "0000_bootstrap"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _create_extensions() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def _ensure_version_table() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(128) NOT NULL PRIMARY KEY
        )
        """
    )


def _has_table(inspector: reflection.Inspector, table: str) -> bool:
    return inspector.has_table(table)


def _has_index(inspector: reflection.Inspector, table: str, name: str) -> bool:
    return any(index["name"] == name for index in inspector.get_indexes(table))


def upgrade() -> None:
    _create_extensions()
    _ensure_version_table()

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=255), nullable=False, unique=True),
            sa.Column("slug", sa.String(length=64), nullable=True, unique=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    if not _has_table(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "tenant_id",
                sa.Integer,
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        )
    if not _has_index(inspector, "users", "ix_users_tenant_id"):
        op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    if not _has_table(inspector, "tickets"):
        op.create_table(
            "tickets",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "tenant_id",
                sa.Integer,
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column(
                "status",
                sa.String(length=32),
                server_default="open",
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
    if not _has_index(inspector, "tickets", "ix_tickets_tenant_id"):
        op.create_index("ix_tickets_tenant_id", "tickets", ["tenant_id"])
    if not _has_index(inspector, "tickets", "ix_tickets_status"):
        op.create_index("ix_tickets_status", "tickets", ["status"])

    if not _has_table(inspector, "messages"):
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column(
                "ticket_id",
                sa.Integer,
                sa.ForeignKey("tickets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
    if not _has_index(
        inspector, "messages", "ix_messages_ticket_created"
    ):
        op.create_index(
            "ix_messages_ticket_created", "messages", ["ticket_id", "created_at"]
        )


def downgrade() -> None:
    op.drop_index("ix_messages_ticket_created", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_tenant_id", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")

    op.drop_table("tenants")
