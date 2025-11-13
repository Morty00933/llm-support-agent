"""Reset legacy schemas to the new bootstrap layout."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision: str = "0001_rebootstrap_schema"
down_revision: str | None = "0001_init"
branch_labels = None
depends_on = None


def _has_column(inspector: reflection.Inspector, table: str, column: str) -> bool:
    if not inspector.has_table(table):
        return False
    return any(col["name"] == column for col in inspector.get_columns(table))


def _schema_is_legacy(inspector: reflection.Inspector) -> bool:
    """Detect whether the existing schema was created by the old migrations."""

    if inspector.has_table("users") and not _has_column(inspector, "users", "password_hash"):
        return True
    if inspector.has_table("tenants") and not _has_column(inspector, "tenants", "slug"):
        return True
    if inspector.has_table("tickets") and _has_column(inspector, "tickets", "subject"):
        return True
    return False


def _load_bootstrap() -> ModuleType:
    module_name = "alembic.versions.0000_bootstrap"
    module = sys.modules.get(module_name)
    if module is not None:
        return module

    path = Path(__file__).resolve().parent / "0000_bootstrap.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load bootstrap migration script")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_bootstrap() -> None:
    bootstrap = _load_bootstrap()
    bootstrap.upgrade()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _schema_is_legacy(inspector):
        op.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        op.execute("CREATE SCHEMA public;")
        inspector = sa.inspect(bind)

    _run_bootstrap()


def downgrade() -> None:
    # The new bootstrap schema is the supported baseline; do not roll back.
    pass
