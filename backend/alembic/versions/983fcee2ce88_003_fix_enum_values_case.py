"""003_fix_enum_values_case

Revision ID: 983fcee2ce88
Revises: 2ca0371578d6
Create Date: 2026-02-11

Fix enum values case: migration 002 added lowercase values but SQLAlchemy
stores enum NAMES (uppercase). We need the uppercase versions.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '983fcee2ce88'
down_revision: Union[str, Sequence[str], None] = '2ca0371578d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add uppercase enum values that SQLAlchemy actually uses."""
    op.execute("COMMIT")

    # Add uppercase versions (the ones SQLAlchemy uses)
    op.execute("ALTER TYPE user_company_status ADD VALUE IF NOT EXISTS 'REMOVED'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'ROLE_CHANGED'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'USER_INVITED'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'USER_REMOVED'")

    op.execute("BEGIN")


def downgrade() -> None:
    """PostgreSQL cannot remove enum values. No-op."""
    pass
