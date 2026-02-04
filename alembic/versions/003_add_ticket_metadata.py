"""add metadata_json to tickets

Revision ID: 003_add_ticket_metadata
Revises: 002_kb_unique_constraint
Create Date: 2025-12-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '003_add_ticket_metadata'
down_revision: Union[str, None] = '002_kb_unique_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata_json column to tickets table."""
    
    # Проверить существует ли таблица
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'tickets' not in inspector.get_table_names():
        print("⚠️  Таблица tickets не существует, пропускаем миграцию")
        return
    
    # Проверить существует ли колонка
    columns = [col['name'] for col in inspector.get_columns('tickets')]
    
    if 'metadata_json' in columns:
        print("✅ Колонка metadata_json уже существует, пропускаем")
        return
    
    # Добавить колонку
    op.add_column(
        'tickets',
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True)
    )
    print("✅ Колонка metadata_json добавлена в tickets")


def downgrade() -> None:
    """Remove metadata_json column from tickets table."""
    
    # Проверить существует ли таблица
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'tickets' not in inspector.get_table_names():
        print("⚠️  Таблица tickets не существует, пропускаем откат")
        return
    
    # Проверить существует ли колонка
    columns = [col['name'] for col in inspector.get_columns('tickets')]
    
    if 'metadata_json' in columns:
        op.drop_column('tickets', 'metadata_json')
        print("✅ Колонка metadata_json удалена из tickets")
    else:
        print("⚠️  Колонка metadata_json не найдена, пропускаем")