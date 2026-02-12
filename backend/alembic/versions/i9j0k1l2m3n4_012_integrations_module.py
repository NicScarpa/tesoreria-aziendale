"""012_integrations_module

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-02-12 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create integrations module tables and enums."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE open_banking_provider AS ENUM (
                'nordigen_gocardless', 'tink', 'salt_edge',
                'cbi_globe', 'fabrick', 'generico'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE open_banking_connection_status AS ENUM (
                'in_attesa_consenso', 'attiva', 'scaduta', 'revocata', 'errore'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE sync_frequency AS ENUM (
                'ogni_ora', 'ogni_6_ore', 'giornaliero', 'manuale'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE sync_log_status AS ENUM ('successo', 'parziale', 'errore');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE invoice_source AS ENUM (
                'cassetto_fiscale', 'upload_xml', 'sdi_api', 'altro'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE invoice_document_type AS ENUM (
                'fattura_vendita', 'fattura_acquisto',
                'nota_credito_vendita', 'nota_credito_acquisto', 'autofattura'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE invoice_status AS ENUM (
                'importata', 'elaborata', 'scadenza_creata', 'errore', 'ignorata'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE invoice_batch_source AS ENUM (
                'cassetto_fiscale', 'upload_multiplo', 'sdi_api'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE invoice_batch_status AS ENUM (
                'in_corso', 'completato', 'completato_con_errori', 'fallito'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE integration_type AS ENUM (
                'open_banking', 'fatture_elettroniche', 'cbi_corporate_banking'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE integration_connection_status AS ENUM (
                'non_configurata', 'configurata', 'connessa', 'errore'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE webhook_type AS ENUM (
                'open_banking_sync', 'sdi_notifica', 'pagamento_esito', 'generico'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- integration_configs ---
    op.create_table(
        "integration_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("integration_type", postgresql.ENUM(
            "open_banking", "fatture_elettroniche", "cbi_corporate_banking",
            name="integration_type", create_type=False,
        ), nullable=False),
        sa.Column("status", postgresql.ENUM(
            "non_configurata", "configurata", "connessa", "errore",
            name="integration_connection_status", create_type=False,
        ), nullable=False, server_default="non_configurata"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "integration_type", name="uq_integration_configs_company_type"),
    )
    op.create_index("ix_integration_configs_company_id", "integration_configs", ["company_id"])

    # --- webhook_endpoints ---
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("tipo", postgresql.ENUM(
            "open_banking_sync", "sdi_notifica", "pagamento_esito", "generico",
            name="webhook_type", create_type=False,
        ), nullable=False),
        sa.Column("url_path", sa.String(255), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url_path", name="uq_webhook_endpoints_url_path"),
    )
    op.create_index("ix_webhook_endpoints_company_id", "webhook_endpoints", ["company_id"])
    op.create_index("ix_webhook_endpoints_company_tipo", "webhook_endpoints", ["company_id", "tipo"])

    # --- open_banking_connections ---
    op.create_table(
        "open_banking_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=True),
        sa.Column("provider", postgresql.ENUM(
            "nordigen_gocardless", "tink", "salt_edge",
            "cbi_globe", "fabrick", "generico",
            name="open_banking_provider", create_type=False,
        ), nullable=False),
        sa.Column("provider_connection_id", sa.String(255), nullable=True),
        sa.Column("provider_account_id", sa.String(255), nullable=True),
        sa.Column("institution_id", sa.String(255), nullable=True),
        sa.Column("institution_nome", sa.String(255), nullable=True),
        sa.Column("institution_logo_url", sa.String(500), nullable=True),
        sa.Column("stato", postgresql.ENUM(
            "in_attesa_consenso", "attiva", "scaduta", "revocata", "errore",
            name="open_banking_connection_status", create_type=False,
        ), nullable=False, server_default="in_attesa_consenso"),
        sa.Column("consenso_id", sa.String(255), nullable=True),
        sa.Column("consenso_scadenza", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consenso_creato_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prossimo_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frequenza_sync", postgresql.ENUM(
            "ogni_ora", "ogni_6_ore", "giornaliero", "manuale",
            name="sync_frequency", create_type=False,
        ), nullable=False, server_default="giornaliero"),
        sa.Column("sync_attivo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("errore_ultimo", sa.Text(), nullable=True),
        sa.Column("errore_conteggio", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_provider", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ob_connections_company_id", "open_banking_connections", ["company_id"])
    op.create_index("ix_ob_connections_company_stato", "open_banking_connections", ["company_id", "stato"])
    op.create_index("ix_ob_connections_company_bank_account", "open_banking_connections", ["company_id", "bank_account_id"])
    op.create_index("ix_ob_connections_prossimo_sync", "open_banking_connections", ["prossimo_sync", "sync_attivo", "stato"])

    # --- open_banking_sync_logs ---
    op.create_table(
        "open_banking_sync_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("connection_id", sa.UUID(), nullable=False),
        sa.Column("data_sync", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("stato", postgresql.ENUM(
            "successo", "parziale", "errore",
            name="sync_log_status", create_type=False,
        ), nullable=False),
        sa.Column("movimenti_scaricati", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("movimenti_nuovi", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("movimenti_duplicati", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saldo_aggiornato", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("periodo_da", sa.DateTime(timezone=True), nullable=True),
        sa.Column("periodo_a", sa.DateTime(timezone=True), nullable=True),
        sa.Column("durata_ms", sa.Integer(), nullable=True),
        sa.Column("errore_dettaglio", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["connection_id"], ["open_banking_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ob_sync_logs_connection_id", "open_banking_sync_logs", ["connection_id"])
    op.create_index("ix_ob_sync_logs_connection_data", "open_banking_sync_logs", ["connection_id", "data_sync"])

    # --- invoice_import_batches ---
    op.create_table(
        "invoice_import_batches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("fonte", postgresql.ENUM(
            "cassetto_fiscale", "upload_multiplo", "sdi_api",
            name="invoice_batch_source", create_type=False,
        ), nullable=False),
        sa.Column("data_import", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("totale_fatture", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fatture_importate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fatture_errore", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fatture_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stato", postgresql.ENUM(
            "in_corso", "completato", "completato_con_errori", "fallito",
            name="invoice_batch_status", create_type=False,
        ), nullable=False, server_default="in_corso"),
        sa.Column("importato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["importato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_import_batches_company_id", "invoice_import_batches", ["company_id"])
    op.create_index("ix_invoice_import_batches_company_data", "invoice_import_batches", ["company_id", "data_import"])

    # --- invoice_imports ---
    op.create_table(
        "invoice_imports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("batch_id", sa.UUID(), nullable=True),
        sa.Column("fonte", postgresql.ENUM(
            "cassetto_fiscale", "upload_xml", "sdi_api", "altro",
            name="invoice_source", create_type=False,
        ), nullable=False),
        sa.Column("tipo_documento", postgresql.ENUM(
            "fattura_vendita", "fattura_acquisto",
            "nota_credito_vendita", "nota_credito_acquisto", "autofattura",
            name="invoice_document_type", create_type=False,
        ), nullable=False),
        sa.Column("stato", postgresql.ENUM(
            "importata", "elaborata", "scadenza_creata", "errore", "ignorata",
            name="invoice_status", create_type=False,
        ), nullable=False, server_default="importata"),
        sa.Column("numero_fattura", sa.String(100), nullable=True),
        sa.Column("data_fattura", sa.Date(), nullable=True),
        sa.Column("cedente_denominazione", sa.String(255), nullable=True),
        sa.Column("cedente_piva", sa.String(20), nullable=True),
        sa.Column("cedente_cf", sa.String(20), nullable=True),
        sa.Column("cessionario_denominazione", sa.String(255), nullable=True),
        sa.Column("cessionario_piva", sa.String(20), nullable=True),
        sa.Column("importo_totale", sa.Numeric(15, 2), nullable=True),
        sa.Column("imponibile_totale", sa.Numeric(15, 2), nullable=True),
        sa.Column("iva_totale", sa.Numeric(15, 2), nullable=True),
        sa.Column("valuta", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("condizioni_pagamento", sa.String(100), nullable=True),
        sa.Column("modalita_pagamento", sa.String(100), nullable=True),
        sa.Column("data_scadenza_pagamento", sa.Date(), nullable=True),
        sa.Column("iban_pagamento", sa.String(34), nullable=True),
        sa.Column("xml_file_path", sa.String(500), nullable=True),
        sa.Column("xml_file_nome", sa.String(255), nullable=True),
        sa.Column("pdf_allegato_path", sa.String(500), nullable=True),
        sa.Column("identificativo_sdi", sa.String(100), nullable=True),
        sa.Column("schedule_id", sa.UUID(), nullable=True),
        sa.Column("counterparty_id", sa.UUID(), nullable=True),
        sa.Column("expected_transaction_id", sa.UUID(), nullable=True),
        sa.Column("errore_dettaglio", sa.Text(), nullable=True),
        sa.Column("elaborato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("data_importazione", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("data_elaborazione", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_id"], ["invoice_import_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["expected_transaction_id"], ["expected_transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["elaborato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_imports_company_id", "invoice_imports", ["company_id"])
    op.create_index("ix_invoice_imports_company_tipo_stato", "invoice_imports", ["company_id", "tipo_documento", "stato"])
    op.create_index("ix_invoice_imports_company_data", "invoice_imports", ["company_id", "data_fattura"])
    op.create_index("ix_invoice_imports_cedente_piva", "invoice_imports", ["cedente_piva", "company_id"])
    op.create_index("ix_invoice_imports_numero_cedente", "invoice_imports", ["numero_fattura", "cedente_piva", "company_id"])
    # Conditional unique index for SDI identifier
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_invoice_imports_sdi
        ON invoice_imports (identificativo_sdi)
        WHERE identificativo_sdi IS NOT NULL;
    """)


def downgrade() -> None:
    """Drop integrations module tables and enums."""
    op.drop_table("invoice_imports")
    op.drop_table("invoice_import_batches")
    op.drop_table("open_banking_sync_logs")
    op.drop_table("open_banking_connections")
    op.drop_table("webhook_endpoints")
    op.drop_table("integration_configs")

    sa.Enum(name="webhook_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="integration_connection_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="integration_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoice_batch_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoice_batch_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoice_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoice_document_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="invoice_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sync_log_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sync_frequency").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="open_banking_connection_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="open_banking_provider").drop(op.get_bind(), checkfirst=True)
