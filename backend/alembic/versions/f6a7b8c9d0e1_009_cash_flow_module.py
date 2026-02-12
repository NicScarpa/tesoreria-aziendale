"""009_cash_flow_module

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-11 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cash flow module tables and enums."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE forecast_status AS ENUM ('bozza', 'attiva', 'archiviata');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE forecast_type AS ENUM ('base', 'ottimistico', 'pessimistico', 'personalizzato');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE cash_flow_line_type AS ENUM ('entrata', 'uscita');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE cash_flow_source AS ENUM (
                'movimento_reale', 'scadenza', 'pagamento_pianificato',
                'ricorrenza', 'manuale', 'stima_storica'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE confidence_level AS ENUM ('certa', 'alta', 'media', 'bassa');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE scenario_adjustment_type AS ENUM (
                'aggiunta', 'rimozione', 'modifica_importo', 'spostamento_data'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE cash_flow_alert_type AS ENUM (
                'sotto_soglia_minima', 'sopra_soglia_massima',
                'saldo_negativo', 'varianza_alta'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE alert_status AS ENUM ('attivo', 'risolto', 'ignorato');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- cash_flow_forecasts ---
    op.create_table(
        "cash_flow_forecasts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("creato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("data_inizio", sa.Date(), nullable=False),
        sa.Column("data_fine", sa.Date(), nullable=False),
        sa.Column("saldo_iniziale", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("saldo_finale_previsto", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("totale_entrate_previste", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("totale_uscite_previste", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("stato", postgresql.ENUM("bozza", "attiva", "archiviata", name="forecast_status", create_type=False), nullable=False, server_default="bozza"),
        sa.Column("tipo", postgresql.ENUM("base", "ottimistico", "pessimistico", "personalizzato", name="forecast_type", create_type=False), nullable=False, server_default="base"),
        sa.Column("parametri", postgresql.JSONB(), nullable=True),
        sa.Column("is_auto", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_flow_forecasts_company_id", "cash_flow_forecasts", ["company_id"])
    op.create_index("ix_cf_forecasts_company_stato", "cash_flow_forecasts", ["company_id", "stato"])
    op.create_index("ix_cf_forecasts_company_auto", "cash_flow_forecasts", ["company_id", "is_auto"])
    op.create_index("ix_cf_forecasts_company_periodo", "cash_flow_forecasts", ["company_id", "data_inizio", "data_fine"])

    # --- cash_flow_forecast_lines ---
    op.create_table(
        "cash_flow_forecast_lines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("forecast_id", sa.UUID(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("tipo", postgresql.ENUM("entrata", "uscita", name="cash_flow_line_type", create_type=False), nullable=False),
        sa.Column("importo", sa.Numeric(15, 2), nullable=False),
        sa.Column("categoria", sa.String(255), nullable=True),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("fonte", postgresql.ENUM("movimento_reale", "scadenza", "pagamento_pianificato", "ricorrenza", "manuale", "stima_storica", name="cash_flow_source", create_type=False), nullable=False),
        sa.Column("fonte_id", sa.String(255), nullable=True),
        sa.Column("confidenza", postgresql.ENUM("certa", "alta", "media", "bassa", name="confidence_level", create_type=False), nullable=False, server_default="media"),
        sa.Column("saldo_progressivo", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("is_realizzata", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("varianza", sa.Numeric(15, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["forecast_id"], ["cash_flow_forecasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cf_lines_forecast_data", "cash_flow_forecast_lines", ["forecast_id", "data"])
    op.create_index("ix_cf_lines_forecast_fonte", "cash_flow_forecast_lines", ["forecast_id", "fonte"])
    op.create_index("ix_cf_lines_forecast_tipo_data", "cash_flow_forecast_lines", ["forecast_id", "tipo", "data"])
    op.create_index("ix_cf_lines_fonte_id", "cash_flow_forecast_lines", ["fonte_id"])

    # --- cash_flow_scenarios ---
    op.create_table(
        "cash_flow_scenarios",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("forecast_id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("tipo_aggiustamento", postgresql.ENUM("aggiunta", "rimozione", "modifica_importo", "spostamento_data", name="scenario_adjustment_type", create_type=False), nullable=False),
        sa.Column("data_originale", sa.Date(), nullable=True),
        sa.Column("data_modificata", sa.Date(), nullable=True),
        sa.Column("importo_originale", sa.Numeric(15, 2), nullable=True),
        sa.Column("importo_modificato", sa.Numeric(15, 2), nullable=True),
        sa.Column("tipo_movimento", postgresql.ENUM("entrata", "uscita", name="cash_flow_line_type", create_type=False), nullable=True),
        sa.Column("categoria", sa.String(255), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["forecast_id"], ["cash_flow_forecasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cf_scenarios_forecast_attivo", "cash_flow_scenarios", ["forecast_id", "attivo"])

    # --- cash_flow_alerts ---
    op.create_table(
        "cash_flow_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("forecast_id", sa.UUID(), nullable=True),
        sa.Column("tipo", postgresql.ENUM("sotto_soglia_minima", "sopra_soglia_massima", "saldo_negativo", "varianza_alta", name="cash_flow_alert_type", create_type=False), nullable=False),
        sa.Column("data_prevista", sa.Date(), nullable=False),
        sa.Column("saldo_previsto", sa.Numeric(15, 2), nullable=False),
        sa.Column("soglia", sa.Numeric(15, 2), nullable=False),
        sa.Column("messaggio", sa.Text(), nullable=False),
        sa.Column("stato", postgresql.ENUM("attivo", "risolto", "ignorato", name="alert_status", create_type=False), nullable=False, server_default="attivo"),
        sa.Column("notificato", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notificato_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["forecast_id"], ["cash_flow_forecasts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_flow_alerts_company_id", "cash_flow_alerts", ["company_id"])
    op.create_index("ix_cf_alerts_company_stato_data", "cash_flow_alerts", ["company_id", "stato", "data_prevista"])
    op.create_index("ix_cf_alerts_company_tipo_stato", "cash_flow_alerts", ["company_id", "tipo", "stato"])


def downgrade() -> None:
    """Drop cash flow module tables and enums."""
    op.drop_table("cash_flow_alerts")
    op.drop_table("cash_flow_scenarios")
    op.drop_table("cash_flow_forecast_lines")
    op.drop_table("cash_flow_forecasts")

    sa.Enum(name="alert_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cash_flow_alert_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="scenario_adjustment_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="confidence_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cash_flow_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cash_flow_line_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="forecast_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="forecast_status").drop(op.get_bind(), checkfirst=True)
