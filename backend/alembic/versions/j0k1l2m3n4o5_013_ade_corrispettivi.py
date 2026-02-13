"""013_ade_corrispettivi

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-02-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, Sequence[str], None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new IntegrationType value (Postgres enum) - must run outside txn.
    op.execute("COMMIT")
    try:
        op.execute("ALTER TYPE integration_type ADD VALUE 'agenzia_entrate'")
    except Exception as e:
        # Ignore "already exists" errors (idempotent deploys).
        if "already exists" not in str(e):
            raise
    op.execute("BEGIN")

    # --- receipt_imports ---
    op.create_table(
        "receipt_imports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("time_rilevazione", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gross_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("net_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("vat_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("source", sa.String(50), nullable=False, server_default="agenzia_entrate"),
        sa.Column("status", sa.String(50), nullable=False, server_default="imported"),
        sa.Column("raw_attachment_path", sa.String(500), nullable=True),
        sa.Column("errore_dettaglio", sa.Text(), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "idempotency_key", name="uq_receipt_imports_company_idempotency"),
    )
    op.create_index("ix_receipt_imports_company_id", "receipt_imports", ["company_id"])
    op.create_index("ix_receipt_imports_business_date", "receipt_imports", ["business_date"])
    op.create_index("ix_receipt_imports_external_id", "receipt_imports", ["external_id"])
    op.create_index("ix_receipt_imports_device_id", "receipt_imports", ["device_id"])
    op.create_index("ix_receipt_imports_company_date", "receipt_imports", ["company_id", "business_date"])
    op.create_index("ix_receipt_imports_company_external", "receipt_imports", ["company_id", "external_id"])
    op.create_index("ix_receipt_imports_company_device_date", "receipt_imports", ["company_id", "device_id", "business_date"])

    # --- ade_sync_logs ---
    op.create_table(
        "ade_sync_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ade_sync_logs_company_id", "ade_sync_logs", ["company_id"])
    op.create_index("ix_ade_sync_logs_company_scope_started", "ade_sync_logs", ["company_id", "scope", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_ade_sync_logs_company_scope_started", table_name="ade_sync_logs")
    op.drop_index("ix_ade_sync_logs_company_id", table_name="ade_sync_logs")
    op.drop_table("ade_sync_logs")

    op.drop_index("ix_receipt_imports_company_device_date", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_company_external", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_company_date", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_device_id", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_external_id", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_business_date", table_name="receipt_imports")
    op.drop_index("ix_receipt_imports_company_id", table_name="receipt_imports")
    op.drop_table("receipt_imports")

    # NOTE: Postgres enum values are not removed on downgrade (non-trivial).

