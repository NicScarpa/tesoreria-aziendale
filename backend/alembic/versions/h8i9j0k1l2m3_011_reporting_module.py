"""011_reporting_module

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-11 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, Sequence[str], None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reporting module tables and enums."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE report_type AS ENUM (
                'saldi_conti', 'movimenti', 'entrate_uscite',
                'riconciliazione', 'scadenzario', 'aging',
                'cash_flow', 'pagamenti', 'controparte', 'personalizzato'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE report_format AS ENUM ('pdf', 'xlsx', 'csv');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE report_execution_status AS ENUM (
                'in_coda', 'in_generazione', 'completato', 'errore'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE report_frequency AS ENUM (
                'giornaliero', 'settimanale', 'mensile', 'trimestrale'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- report_definitions ---
    op.create_table(
        "report_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("tipo", postgresql.ENUM(
            "saldi_conti", "movimenti", "entrate_uscite",
            "riconciliazione", "scadenzario", "aging",
            "cash_flow", "pagamenti", "controparte", "personalizzato",
            name="report_type", create_type=False,
        ), nullable=False),
        sa.Column("formato_default", postgresql.ENUM(
            "pdf", "xlsx", "csv",
            name="report_format", create_type=False,
        ), nullable=False, server_default="pdf"),
        sa.Column("parametri_default", postgresql.JSONB(), nullable=True),
        sa.Column("layout", postgresql.JSONB(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_preferito", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_definitions_company_tipo", "report_definitions", ["company_id", "tipo"])
    op.create_index("ix_report_definitions_company_preferito", "report_definitions", ["company_id", "is_preferito"])
    op.create_index("ix_report_definitions_company_system", "report_definitions", ["company_id", "is_system"])

    # --- report_executions ---
    op.create_table(
        "report_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("report_definition_id", sa.UUID(), nullable=True),
        sa.Column("generato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("formato", postgresql.ENUM(
            "pdf", "xlsx", "csv",
            name="report_format", create_type=False,
        ), nullable=False),
        sa.Column("stato", postgresql.ENUM(
            "in_coda", "in_generazione", "completato", "errore",
            name="report_execution_status", create_type=False,
        ), nullable=False, server_default="in_coda"),
        sa.Column("parametri", postgresql.JSONB(), nullable=True),
        sa.Column("risultato", postgresql.JSONB(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("errore", sa.Text(), nullable=True),
        sa.Column("righe_totali", sa.Integer(), nullable=True),
        sa.Column("data_generazione", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("data_completamento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_scadenza_file", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_definition_id"], ["report_definitions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["generato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_executions_company_data", "report_executions", ["company_id", sa.text("data_generazione DESC")])
    op.create_index("ix_report_executions_company_definition", "report_executions", ["company_id", "report_definition_id"])
    op.create_index("ix_report_executions_stato", "report_executions", ["stato"])
    op.create_index("ix_report_executions_scadenza", "report_executions", ["data_scadenza_file"])

    # --- report_schedules ---
    op.create_table(
        "report_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("report_definition_id", sa.UUID(), nullable=False),
        sa.Column("creato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("frequenza", postgresql.ENUM(
            "giornaliero", "settimanale", "mensile", "trimestrale",
            name="report_frequency", create_type=False,
        ), nullable=False),
        sa.Column("formato", postgresql.ENUM(
            "pdf", "xlsx", "csv",
            name="report_format", create_type=False,
        ), nullable=False, server_default="pdf"),
        sa.Column("parametri", postgresql.JSONB(), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("prossima_esecuzione", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultima_esecuzione", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_definition_id"], ["report_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_schedules_company_attivo", "report_schedules", ["company_id", "attivo"])
    op.create_index("ix_report_schedules_prossima_attivo", "report_schedules", ["prossima_esecuzione", "attivo"])


def downgrade() -> None:
    """Drop reporting module tables and enums."""
    op.drop_table("report_schedules")
    op.drop_table("report_executions")
    op.drop_table("report_definitions")

    sa.Enum(name="report_frequency").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_execution_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_format").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_type").drop(op.get_bind(), checkfirst=True)
