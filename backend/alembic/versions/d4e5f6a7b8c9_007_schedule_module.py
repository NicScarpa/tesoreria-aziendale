"""007_schedule_module

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-11 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create schedule module tables, enums, and alter expected_transactions."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE schedule_type AS ENUM ('attiva', 'passiva');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE schedule_status AS ENUM ('aperta', 'parzialmente_pagata', 'pagata', 'scaduta', 'annullata');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE document_type AS ENUM (
                'fattura_vendita', 'fattura_acquisto', 'nota_credito', 'nota_debito',
                'stipendio', 'tassa_f24', 'contributo', 'affitto', 'utenza',
                'rata_prestito', 'altro'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE schedule_priority AS ENUM ('bassa', 'normale', 'alta', 'urgente');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE recurrence_type AS ENUM (
                'settimanale', 'mensile', 'bimestrale', 'trimestrale', 'semestrale', 'annuale'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE schedule_source AS ENUM ('manuale', 'import_csv', 'import_fatture_sdi', 'ricorrenza_auto');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE payment_method AS ENUM ('bonifico', 'ri_ba', 'sdd', 'carta', 'contanti', 'f24', 'altro');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE reminder_type AS ENUM ('email', 'in_app', 'entrambi');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- schedules ---
    op.create_table(
        "schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("tipo", postgresql.ENUM("attiva", "passiva", name="schedule_type", create_type=False), nullable=False),
        sa.Column("stato", postgresql.ENUM("aperta", "parzialmente_pagata", "pagata", "scaduta", "annullata",
                                            name="schedule_status", create_type=False),
                  nullable=False, server_default="aperta"),
        sa.Column("descrizione", sa.String(500), nullable=False),
        sa.Column("importo_totale", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("importo_pagato", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("valuta", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("data_scadenza", sa.Date(), nullable=False),
        sa.Column("data_emissione", sa.Date(), nullable=True),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        # Documento
        sa.Column("tipo_documento", postgresql.ENUM(
            "fattura_vendita", "fattura_acquisto", "nota_credito", "nota_debito",
            "stipendio", "tassa_f24", "contributo", "affitto", "utenza", "rata_prestito", "altro",
            name="document_type", create_type=False), nullable=False, server_default="altro"),
        sa.Column("numero_documento", sa.String(100), nullable=True),
        sa.Column("riferimento_documento", sa.String(255), nullable=True),
        # Controparte
        sa.Column("controparte_nome", sa.String(255), nullable=True),
        sa.Column("controparte_iban", sa.String(34), nullable=True),
        sa.Column("counterparty_id", sa.UUID(), nullable=True),
        # Conto bancario
        sa.Column("bank_account_id", sa.UUID(), nullable=True),
        # Priorita
        sa.Column("priorita", postgresql.ENUM("bassa", "normale", "alta", "urgente",
                                               name="schedule_priority", create_type=False),
                  nullable=False, server_default="normale"),
        sa.Column("metodo_pagamento", postgresql.ENUM(
            "bonifico", "ri_ba", "sdd", "carta", "contanti", "f24", "altro",
            name="payment_method", create_type=False), nullable=True),
        sa.Column("categoria_id", sa.UUID(), nullable=True),
        # Origine
        sa.Column("source", postgresql.ENUM("manuale", "import_csv", "import_fatture_sdi", "ricorrenza_auto",
                                             name="schedule_source", create_type=False),
                  nullable=False, server_default="manuale"),
        # Ricorrenza
        sa.Column("is_ricorrente", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ricorrenza_tipo", postgresql.ENUM(
            "settimanale", "mensile", "bimestrale", "trimestrale", "semestrale", "annuale",
            name="recurrence_type", create_type=False), nullable=True),
        sa.Column("ricorrenza_fine", sa.Date(), nullable=True),
        sa.Column("ricorrenza_prossima_generazione", sa.Date(), nullable=True),
        sa.Column("ricorrenza_parent_id", sa.UUID(), nullable=True),
        sa.Column("ricorrenza_attiva", sa.Boolean(), nullable=False, server_default="true"),
        # Expected transaction link
        sa.Column("expected_transaction_id", sa.UUID(), nullable=True),
        # Note e user
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["expected_transaction_id"], ["expected_transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ricorrenza_parent_id"], ["schedules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedules_company_id"), "schedules", ["company_id"])
    op.create_index(op.f("ix_schedules_data_scadenza"), "schedules", ["data_scadenza"])
    op.create_index(op.f("ix_schedules_bank_account_id"), "schedules", ["bank_account_id"])
    op.create_index(op.f("ix_schedules_counterparty_id"), "schedules", ["counterparty_id"])
    op.create_index("ix_schedules_company_stato_scadenza", "schedules", ["company_id", "stato", "data_scadenza"])
    op.create_index("ix_schedules_company_tipo_stato", "schedules", ["company_id", "tipo", "stato"])
    op.create_index("ix_schedules_company_counterparty", "schedules", ["company_id", "counterparty_id"])
    op.create_index("ix_schedules_company_data_scadenza", "schedules", ["company_id", "data_scadenza"])
    op.create_index("ix_schedules_company_stato_priorita", "schedules", ["company_id", "stato", "priorita"])
    op.create_index("ix_schedules_company_ricorrente_prossima", "schedules",
                    ["company_id", "is_ricorrente", "ricorrenza_prossima_generazione"])

    # --- schedule_payments ---
    op.create_table(
        "schedule_payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("schedule_id", sa.UUID(), nullable=False),
        sa.Column("importo", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column("metodo", postgresql.ENUM(
            "bonifico", "ri_ba", "sdd", "carta", "contanti", "f24", "altro",
            name="payment_method", create_type=False), nullable=True),
        sa.Column("riferimento", sa.String(255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("reconciliation_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_payments_schedule_id"), "schedule_payments", ["schedule_id"])

    # --- schedule_reminders ---
    op.create_table(
        "schedule_reminders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("schedule_id", sa.UUID(), nullable=False),
        sa.Column("giorni_prima", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("tipo", postgresql.ENUM("email", "in_app", "entrambi",
                                           name="reminder_type", create_type=False),
                  nullable=False, server_default="in_app"),
        sa.Column("messaggio", sa.Text(), nullable=True),
        sa.Column("inviato", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_invio", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_reminders_schedule_id"), "schedule_reminders", ["schedule_id"])

    # --- schedule_attachments ---
    op.create_table(
        "schedule_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("schedule_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_by_user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_attachments_schedule_id"), "schedule_attachments", ["schedule_id"])

    # --- ALTER expected_transactions: add FK constraint on schedule_id ---
    op.create_foreign_key(
        "fk_expected_transactions_schedule_id",
        "expected_transactions", "schedules",
        ["schedule_id"], ["id"],
        ondelete="SET NULL",
    )

    # --- Seed data ---
    _seed_data()


def _seed_data() -> None:
    """Insert seed schedules with mixed types and statuses."""
    from datetime import date, timedelta

    today = date.today()

    op.execute(f"""
        INSERT INTO schedules
            (id, company_id, tipo, stato, descrizione, importo_totale, importo_pagato,
             valuta, data_scadenza, data_emissione, data_pagamento,
             tipo_documento, numero_documento, riferimento_documento,
             controparte_nome, controparte_iban, bank_account_id,
             priorita, metodo_pagamento, source,
             is_ricorrente, ricorrenza_tipo, ricorrenza_prossima_generazione, ricorrenza_attiva,
             note, created_at, updated_at)
        SELECT
            gen_random_uuid(), c.id,
            s.tipo::schedule_type, s.stato::schedule_status,
            s.descrizione, s.importo_totale, s.importo_pagato,
            'EUR', s.data_scadenza, s.data_emissione, s.data_pagamento,
            s.tipo_documento::document_type, s.numero_documento, s.riferimento_documento,
            s.controparte_nome, s.controparte_iban, ba.id,
            s.priorita::schedule_priority,
            CASE WHEN s.metodo_pagamento IS NOT NULL THEN s.metodo_pagamento::payment_method ELSE NULL END,
            'manuale'::schedule_source,
            s.is_ricorrente,
            CASE WHEN s.ricorrenza_tipo IS NOT NULL THEN s.ricorrenza_tipo::recurrence_type ELSE NULL END,
            s.ricorrenza_prossima,
            COALESCE(s.ricorrenza_attiva, true),
            s.note, NOW(), NOW()
        FROM companies c
        CROSS JOIN LATERAL (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1) ba
        CROSS JOIN (VALUES
            -- 5 Fatture vendita (attive, da incassare)
            ('attiva', 'aperta', 'Fattura vendita prodotti Cliente Gamma', 5000.00, 0,
             '{today + timedelta(days=10)}'::date, '{today - timedelta(days=5)}'::date, NULL::date,
             'fattura_vendita', 'FV-2026/001', 'FV-2026/001',
             'Cliente Gamma SRL', 'IT60X0542811101000000333333',
             'normale', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            ('attiva', 'aperta', 'Fattura vendita servizi Cliente Delta', 3200.00, 0,
             '{today + timedelta(days=15)}'::date, '{today - timedelta(days=3)}'::date, NULL::date,
             'fattura_vendita', 'FV-2026/002', 'FV-2026/002',
             'Cliente Delta SpA', 'IT60X0542811101000000444444',
             'alta', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            ('attiva', 'parzialmente_pagata', 'Fattura vendita progetto Cliente Theta', 7500.00, 3000.00,
             '{today + timedelta(days=5)}'::date, '{today - timedelta(days=20)}'::date, NULL::date,
             'fattura_vendita', 'FV-2026/003', 'FV-2026/003',
             'Cliente Theta SpA', 'IT60X0542811101000000777777',
             'normale', 'bonifico', false, NULL::text, NULL::date, NULL::boolean,
             'Primo acconto ricevuto il 01/02'),

            ('attiva', 'scaduta', 'Fattura vendita scaduta Cliente Zeta', 980.00, 0,
             '{today - timedelta(days=10)}'::date, '{today - timedelta(days=40)}'::date, NULL::date,
             'fattura_vendita', 'FV-2026/004', 'FV-2026/004',
             'Cliente Zeta SRL', 'IT60X0542811101000000555555',
             'urgente', 'bonifico', false, NULL::text, NULL::date, NULL::boolean,
             'Sollecito inviato'),

            ('attiva', 'pagata', 'Fattura vendita completata Cliente Kappa', 2100.00, 2100.00,
             '{today - timedelta(days=5)}'::date, '{today - timedelta(days=35)}'::date, '{today - timedelta(days=5)}'::date,
             'fattura_vendita', 'FV-2026/005', 'FV-2026/005',
             'Cliente Kappa SRL', NULL,
             'normale', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            -- 5 Fatture acquisto (passive, da pagare)
            ('passiva', 'aperta', 'Fattura acquisto materiali Fornitore Alpha', 2500.00, 0,
             '{today + timedelta(days=7)}'::date, '{today - timedelta(days=10)}'::date, NULL::date,
             'fattura_acquisto', 'FT-2026/001', 'FT-2026/001',
             'Fornitore Alpha SRL', 'IT60X0542811101000000111111',
             'alta', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            ('passiva', 'aperta', 'Fattura servizi consulenza Fornitore Beta', 1800.50, 0,
             '{today + timedelta(days=12)}'::date, '{today - timedelta(days=8)}'::date, NULL::date,
             'fattura_acquisto', 'FT-2026/002', 'FT-2026/002',
             'Fornitore Beta SpA', 'IT60X0542811101000000222222',
             'normale', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            ('passiva', 'parzialmente_pagata', 'Fattura acquisto macchinari Fornitore Eta', 3100.00, 1000.00,
             '{today + timedelta(days=20)}'::date, '{today - timedelta(days=15)}'::date, NULL::date,
             'fattura_acquisto', 'FT-2026/003', 'FT-2026/003',
             'Fornitore Eta SRL', 'IT60X0542811101000000666666',
             'normale', 'ri_ba', false, NULL::text, NULL::date, NULL::boolean,
             'Prima rata pagata'),

            ('passiva', 'scaduta', 'Nota credito scaduta Fornitore Epsilon', 750.00, 0,
             '{today - timedelta(days=5)}'::date, '{today - timedelta(days=30)}'::date, NULL::date,
             'nota_credito', 'NC-2026/001', 'NC-2026/001',
             'Fornitore Epsilon SNC', NULL,
             'bassa', NULL, false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            ('passiva', 'pagata', 'Fattura pagata Fornitore Iota', 450.00, 450.00,
             '{today - timedelta(days=3)}'::date, '{today - timedelta(days=25)}'::date, '{today - timedelta(days=3)}'::date,
             'nota_debito', 'ND-2026/001', 'ND-2026/001',
             'Fornitore Iota SAS', NULL,
             'normale', 'bonifico', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            -- 2 Stipendi
            ('passiva', 'aperta', 'Stipendi febbraio 2026', 4500.00, 0,
             '{today + timedelta(days=16)}'::date, NULL::date, NULL::date,
             'stipendio', NULL, NULL,
             'Dipendenti', NULL,
             'alta', 'bonifico', true, 'mensile', '{today + timedelta(days=46)}'::date, true, NULL::text),

            ('passiva', 'pagata', 'Stipendi gennaio 2026', 4500.00, 4500.00,
             '{today - timedelta(days=14)}'::date, NULL::date, '{today - timedelta(days=14)}'::date,
             'stipendio', NULL, NULL,
             'Dipendenti', NULL,
             'alta', 'bonifico', true, 'mensile', NULL::date, true, NULL::text),

            -- 2 Utenze
            ('passiva', 'aperta', 'Bolletta energia elettrica', 320.00, 0,
             '{today + timedelta(days=18)}'::date, '{today - timedelta(days=2)}'::date, NULL::date,
             'utenza', NULL, 'ENEL-2026/02',
             'Enel Energia SpA', NULL,
             'normale', 'sdd', true, 'mensile', '{today + timedelta(days=48)}'::date, true, NULL::text),

            ('passiva', 'aperta', 'Bolletta gas', 185.00, 0,
             '{today + timedelta(days=22)}'::date, '{today - timedelta(days=1)}'::date, NULL::date,
             'utenza', NULL, 'ENI-2026/02',
             'Eni Gas e Luce', NULL,
             'bassa', 'sdd', true, 'bimestrale', '{today + timedelta(days=82)}'::date, true, NULL::text),

            -- 1 Tassa F24
            ('passiva', 'aperta', 'F24 IVA gennaio 2026', 1200.00, 0,
             '{today + timedelta(days=5)}'::date, NULL::date, NULL::date,
             'tassa_f24', 'F24-2026/01', 'F24-2026/01',
             'Agenzia delle Entrate', NULL,
             'urgente', 'f24', false, NULL::text, NULL::date, NULL::boolean, NULL::text),

            -- 1 Affitto ricorrente
            ('passiva', 'aperta', 'Canone affitto ufficio marzo', 1500.00, 0,
             '{today + timedelta(days=25)}'::date, NULL::date, NULL::date,
             'affitto', NULL, 'AFF-2026/03',
             'Immobiliare Rossi SRL', 'IT60X0542811101000000888888',
             'normale', 'bonifico', true, 'mensile', '{today + timedelta(days=55)}'::date, true, NULL::text),

            -- 1 Scaduta da incassare
            ('attiva', 'scaduta', 'Nota debito scaduta Cliente Lambda', 1250.00, 0,
             '{today - timedelta(days=15)}'::date, '{today - timedelta(days=45)}'::date, NULL::date,
             'nota_debito', 'ND-2026/010', 'ND-2026/010',
             'Cliente Lambda SRL', NULL,
             'alta', NULL, false, NULL::text, NULL::date, NULL::boolean,
             'Secondo sollecito')
        ) AS s(tipo, stato, descrizione, importo_totale, importo_pagato,
               data_scadenza, data_emissione, data_pagamento,
               tipo_documento, numero_documento, riferimento_documento,
               controparte_nome, controparte_iban,
               priorita, metodo_pagamento, is_ricorrente, ricorrenza_tipo,
               ricorrenza_prossima, ricorrenza_attiva, note)
        WHERE EXISTS (SELECT 1 FROM bank_accounts WHERE company_id = c.id)
    """)

    # Insert seed payments for partially paid schedules
    op.execute("""
        INSERT INTO schedule_payments (id, schedule_id, importo, data_pagamento, metodo, riferimento, note, created_at)
        SELECT gen_random_uuid(), s.id, 3000.00, CURRENT_DATE - INTERVAL '10 days', 'bonifico'::payment_method,
               'Acconto FV-2026/003', 'Primo acconto', NOW()
        FROM schedules s WHERE s.riferimento_documento = 'FV-2026/003'
    """)
    op.execute("""
        INSERT INTO schedule_payments (id, schedule_id, importo, data_pagamento, metodo, riferimento, note, created_at)
        SELECT gen_random_uuid(), s.id, 1000.00, CURRENT_DATE - INTERVAL '5 days', 'ri_ba'::payment_method,
               'Prima rata FT-2026/003', 'Prima rata', NOW()
        FROM schedules s WHERE s.riferimento_documento = 'FT-2026/003'
    """)


def downgrade() -> None:
    """Drop schedule module tables and enums."""
    # Remove FK on expected_transactions
    op.drop_constraint("fk_expected_transactions_schedule_id", "expected_transactions", type_="foreignkey")

    # Drop tables
    op.drop_table("schedule_attachments")
    op.drop_table("schedule_reminders")
    op.drop_table("schedule_payments")
    op.drop_table("schedules")

    # Drop enums
    sa.Enum(name="reminder_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_method").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="schedule_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recurrence_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="schedule_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="document_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="schedule_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="schedule_type").drop(op.get_bind(), checkfirst=True)
