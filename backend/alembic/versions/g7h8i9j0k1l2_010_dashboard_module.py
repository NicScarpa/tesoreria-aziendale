"""010_dashboard_module

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-11 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create dashboard module tables and enums."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE widget_type AS ENUM (
                'saldo_totale', 'cash_flow_mini', 'entrate_uscite',
                'scadenze', 'riconciliazione', 'pagamenti_pendenti',
                'alert', 'attivita_recenti', 'azioni_rapide', 'saldi_per_conto'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE widget_size AS ENUM ('small', 'medium', 'large');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- dashboard_widgets ---
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("widget_type", postgresql.ENUM(
            "saldo_totale", "cash_flow_mini", "entrate_uscite",
            "scadenze", "riconciliazione", "pagamenti_pendenti",
            "alert", "attivita_recenti", "azioni_rapide", "saldi_per_conto",
            name="widget_type", create_type=False,
        ), nullable=False),
        sa.Column("posizione", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("colonna", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dimensione", postgresql.ENUM(
            "small", "medium", "large",
            name="widget_size", create_type=False,
        ), nullable=False, server_default="medium"),
        sa.Column("configurazione", postgresql.JSONB(), nullable=True),
        sa.Column("visibile", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "company_id", "widget_type", name="uq_dashboard_widget_user_company_type"),
    )
    op.create_index("ix_dashboard_widgets_user_company", "dashboard_widgets", ["user_id", "company_id"])

    # --- dashboard_snapshots ---
    op.create_table(
        "dashboard_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("saldo_totale", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("entrate_giorno", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("uscite_giorno", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("movimenti_non_riconciliati", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scadenze_scadute_importo", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("scadenze_scadute_conteggio", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pagamenti_da_approvare", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("previsione_30gg", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("alert_attivi", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "data", name="uq_dashboard_snapshot_company_data"),
    )
    op.create_index("ix_dashboard_snapshots_company_data", "dashboard_snapshots", ["company_id", "data"])


def downgrade() -> None:
    """Drop dashboard module tables and enums."""
    op.drop_table("dashboard_snapshots")
    op.drop_table("dashboard_widgets")

    sa.Enum(name="widget_size").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="widget_type").drop(op.get_bind(), checkfirst=True)
