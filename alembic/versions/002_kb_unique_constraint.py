"""add kb_chunks unique constraint

Revision ID: 002_kb_unique_constraint
Revises: 001_initial
Create Date: 2025-12-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '002_kb_unique_constraint'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add UNIQUE constraint on (tenant_id, chunk_hash) - SAFE VERSION."""
    
    # Проверить существует ли таблица kb_chunks
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'kb_chunks' not in inspector.get_table_names():
        print("⚠️  Таблица kb_chunks не существует, пропускаем миграцию")
        return
    
    # Проверить существует ли constraint
    constraints = inspector.get_unique_constraints('kb_chunks')
    constraint_names = [c['name'] for c in constraints]
    
    if 'uq_kb_tenant_hash' in constraint_names:
        print("✅ Constraint uq_kb_tenant_hash уже существует, пропускаем")
        return
    
    # Удалить дубликаты если есть (безопасно)
    try:
        op.execute("""
            DELETE FROM kb_chunks
            WHERE id NOT IN (
                SELECT DISTINCT ON (tenant_id, chunk_hash) id
                FROM kb_chunks
                ORDER BY tenant_id, chunk_hash, updated_at DESC
            )
        """)
        print("✅ Дубликаты удалены")
    except Exception as e:
        print(f"⚠️  Ошибка при удалении дубликатов: {e}")
        # Продолжаем - возможно таблица пустая
    
    # Добавить UNIQUE constraint
    try:
        op.create_unique_constraint(
            'uq_kb_tenant_hash',
            'kb_chunks',
            ['tenant_id', 'chunk_hash']
        )
        print("✅ Constraint uq_kb_tenant_hash добавлен")
    except Exception as e:
        print(f"❌ Ошибка при добавлении constraint: {e}")
        raise


def downgrade() -> None:
    """Remove UNIQUE constraint - SAFE VERSION."""
    
    # Проверить существует ли таблица
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'kb_chunks' not in inspector.get_table_names():
        print("⚠️  Таблица kb_chunks не существует, пропускаем откат")
        return
    
    # Проверить существует ли constraint
    constraints = inspector.get_unique_constraints('kb_chunks')
    constraint_names = [c['name'] for c in constraints]
    
    if 'uq_kb_tenant_hash' in constraint_names:
        op.drop_constraint('uq_kb_tenant_hash', 'kb_chunks', type_='unique')
        print("✅ Constraint uq_kb_tenant_hash удалён")
    else:
        print("⚠️  Constraint uq_kb_tenant_hash не найден, пропускаем")