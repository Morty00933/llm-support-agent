"""Initial migration - creates all tables - FULLY FIXED VERSION

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

ИСПРАВЛЕНИЯ:
- Правильный UniqueConstraint для kb_chunks: (tenant_id, chunk_hash)
- Добавлено поле metadata_json в tickets
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ===== Tenants =====
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(64), unique=True, nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('name'),
    )

    # ===== Users =====
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('role', sa.String(32), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_users_tenant_email', 'users', ['tenant_id', 'email'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'])

    # ===== Tickets =====
    # ИСПРАВЛЕНО: Добавлено поле metadata_json
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(32), server_default='open', nullable=False),
        sa.Column('priority', sa.String(32), server_default='medium', nullable=False),
        sa.Column('source', sa.String(64), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),  # ДОБАВЛЕНО!
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_tickets_tenant', 'tickets', ['tenant_id'])
    op.create_index('ix_tickets_status', 'tickets', ['status'])

    # ===== Messages =====
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_messages_ticket_id', 'messages', ['ticket_id'])

    # ===== KB Chunks =====
    # ИСПРАВЛЕНО: Правильный UniqueConstraint (tenant_id, chunk_hash)
    op.create_table(
        'kb_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('chunk', sa.Text(), nullable=False),
        sa.Column('chunk_hash', sa.String(64), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_current', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        # ИСПРАВЛЕНО: Правильный constraint как в models.py
        sa.UniqueConstraint('tenant_id', 'chunk_hash', name='uq_kb_tenant_hash'),
    )
    op.create_index('ix_kb_tenant_source', 'kb_chunks', ['tenant_id', 'source'])

    # === Векторное поле для pgvector ===
    op.execute("ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS embedding_vector vector(768)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kb_embedding 
        ON kb_chunks USING ivfflat (embedding_vector vector_cosine_ops) 
        WITH (lists = 100)
    """)

    # ===== Ticket External Refs =====
    op.create_table(
        'ticket_external_refs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('system', sa.String(32), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('external_url', sa.String(512), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('system', 'external_id', name='uq_external_ref_system_id'),
    )

    # ===== Integration Sync Logs =====
    op.create_table(
        'integration_sync_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('system', sa.String(32), nullable=False),
        sa.Column('direction', sa.String(16), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('records_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS integration_sync_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS ticket_external_refs CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS tickets CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE")
    op.execute("DROP TABLE IF EXISTS kb_chunks CASCADE")

    # Опционально: убрать расширение
    # op.execute("DROP EXTENSION IF EXISTS vector CASCADE")