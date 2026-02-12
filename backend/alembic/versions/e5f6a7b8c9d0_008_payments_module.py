"""008_payments_module

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-11 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create payment module tables, enums, and seed data."""
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE payment_order_type AS ENUM (
                'sepa_credit_transfer', 'riba', 'sdd', 'f24', 'bonifico_estero'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE payment_order_status AS ENUM (
                'bozza', 'da_approvare', 'approvata', 'file_generato',
                'inviata_banca', 'eseguita', 'rifiutata', 'annullata'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE payment_priority AS ENUM ('normale', 'alta', 'urgente');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE payment_line_status AS ENUM ('inclusa', 'eseguita', 'rifiutata', 'esclusa');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE approval_action AS ENUM ('approvata', 'rifiutata', 'richiesta_modifica');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE sdd_mandate_type AS ENUM ('core', 'b2b');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE sdd_sequence_type AS ENUM ('frst', 'rcur', 'fnal', 'ooff');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE f24_section_type AS ENUM ('erario', 'inps', 'regioni', 'imu_altri_enti');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- payment_orders ---
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=True),
        sa.Column("tipo", postgresql.ENUM(
            "sepa_credit_transfer", "riba", "sdd", "f24", "bonifico_estero",
            name="payment_order_type", create_type=False), nullable=False),
        sa.Column("stato", postgresql.ENUM(
            "bozza", "da_approvare", "approvata", "file_generato",
            "inviata_banca", "eseguita", "rifiutata", "annullata",
            name="payment_order_status", create_type=False),
            nullable=False, server_default="bozza"),
        sa.Column("riferimento_interno", sa.String(50), nullable=False),
        sa.Column("data_esecuzione_richiesta", sa.Date(), nullable=False),
        sa.Column("importo_totale", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("numero_disposizioni", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valuta", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("priorita", postgresql.ENUM(
            "normale", "alta", "urgente",
            name="payment_priority", create_type=False),
            nullable=False, server_default="normale"),
        # SEPA/formato metadata
        sa.Column("metadata_sepa", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB(), nullable=True),
        # File generato
        sa.Column("file_generato_path", sa.String(500), nullable=True),
        sa.Column("file_generato_nome", sa.String(255), nullable=True),
        sa.Column("file_generato_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_esito_path", sa.String(500), nullable=True),
        # Approvazione
        sa.Column("approvato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("data_approvazione", sa.DateTime(timezone=True), nullable=True),
        # Creazione
        sa.Column("creato_da_user_id", sa.UUID(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approvato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creato_da_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("riferimento_interno", "company_id", name="uq_payment_orders_riferimento_company"),
    )
    op.create_index(op.f("ix_payment_orders_company_id"), "payment_orders", ["company_id"])
    op.create_index(op.f("ix_payment_orders_bank_account_id"), "payment_orders", ["bank_account_id"])
    op.create_index("ix_payment_orders_company_stato", "payment_orders", ["company_id", "stato"])
    op.create_index("ix_payment_orders_company_data_esecuzione", "payment_orders",
                    ["company_id", "data_esecuzione_richiesta"])
    op.create_index("ix_payment_orders_company_tipo_stato", "payment_orders", ["company_id", "tipo", "stato"])

    # --- payment_order_lines ---
    op.create_table(
        "payment_order_lines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_order_id", sa.UUID(), nullable=False),
        # Beneficiario
        sa.Column("beneficiario_nome", sa.String(255), nullable=False),
        sa.Column("beneficiario_iban", sa.String(34), nullable=True),
        sa.Column("beneficiario_bic", sa.String(11), nullable=True),
        sa.Column("beneficiario_cf", sa.String(16), nullable=True),
        sa.Column("beneficiario_indirizzo", sa.String(500), nullable=True),
        # Dati pagamento
        sa.Column("importo", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("valuta", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("causale", sa.String(140), nullable=True),
        sa.Column("end_to_end_id", sa.String(35), nullable=True),
        # Stato riga
        sa.Column("stato", postgresql.ENUM(
            "inclusa", "eseguita", "rifiutata", "esclusa",
            name="payment_line_status", create_type=False),
            nullable=False, server_default="inclusa"),
        # FK opzionali
        sa.Column("counterparty_id", sa.UUID(), nullable=True),
        sa.Column("schedule_id", sa.UUID(), nullable=True),
        # Campi RiBa
        sa.Column("riba_numero_ricevuta", sa.String(10), nullable=True),
        sa.Column("riba_data_scadenza", sa.Date(), nullable=True),
        sa.Column("riba_piazza", sa.String(50), nullable=True),
        sa.Column("riba_abi_banca_domiciliataria", sa.String(5), nullable=True),
        sa.Column("riba_cab_banca_domiciliataria", sa.String(5), nullable=True),
        # Campi SDD
        sa.Column("sdd_mandate_id", sa.String(35), nullable=True),
        sa.Column("sdd_mandate_date", sa.Date(), nullable=True),
        sa.Column("sdd_mandate_type", postgresql.ENUM(
            "core", "b2b", name="sdd_mandate_type", create_type=False), nullable=True),
        sa.Column("sdd_sequence_type", postgresql.ENUM(
            "frst", "rcur", "fnal", "ooff", name="sdd_sequence_type", create_type=False), nullable=True),
        # Campi F24
        sa.Column("f24_sezione", postgresql.ENUM(
            "erario", "inps", "regioni", "imu_altri_enti",
            name="f24_section_type", create_type=False), nullable=True),
        sa.Column("f24_codice_tributo", sa.String(10), nullable=True),
        sa.Column("f24_rateazione", sa.String(4), nullable=True),
        sa.Column("f24_anno_riferimento", sa.Integer(), nullable=True),
        sa.Column("f24_mese_riferimento", sa.Integer(), nullable=True),
        sa.Column("f24_importo_debito", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("f24_importo_credito", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("f24_codice_ente", sa.String(10), nullable=True),
        sa.Column("f24_codice_sede", sa.String(10), nullable=True),
        # Metadata
        sa.Column("metadata_extra", postgresql.JSONB(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_order_lines_payment_order_id"), "payment_order_lines", ["payment_order_id"])
    op.create_index(op.f("ix_payment_order_lines_counterparty_id"), "payment_order_lines", ["counterparty_id"])
    op.create_index(op.f("ix_payment_order_lines_schedule_id"), "payment_order_lines", ["schedule_id"])
    op.create_index("ix_payment_order_lines_stato", "payment_order_lines", ["stato"])

    # --- payment_approvals ---
    op.create_table(
        "payment_approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_order_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("azione", postgresql.ENUM(
            "approvata", "rifiutata", "richiesta_modifica",
            name="approval_action", create_type=False), nullable=False),
        sa.Column("commento", sa.Text(), nullable=True),
        sa.Column("data_azione", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_approvals_payment_order_id"), "payment_approvals", ["payment_order_id"])
    op.create_index("ix_payment_approvals_order_data", "payment_approvals",
                    ["payment_order_id", "data_azione"])

    # --- payment_templates ---
    op.create_table(
        "payment_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", postgresql.ENUM(
            "sepa_credit_transfer", "riba", "sdd", "f24", "bonifico_estero",
            name="payment_order_type", create_type=False), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=True),
        sa.Column("dati_template", postgresql.JSONB(), nullable=True),
        sa.Column("ultimo_utilizzo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("volte_utilizzato", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_templates_company_id"), "payment_templates", ["company_id"])
    op.create_index("ix_payment_templates_company_tipo", "payment_templates", ["company_id", "tipo"])

    # --- Seed data ---
    _seed_data()


def _seed_data() -> None:
    """Insert seed payment orders with lines.

    Uses LEFT JOIN on bank_accounts so seed works even without bank accounts.
    Lines use INSERT ... SELECT to only insert when parent order exists.
    """
    from datetime import date, timedelta

    today = date.today()

    # SEPA CT bozza con 3 righe
    op.execute(f"""
        INSERT INTO payment_orders
            (id, company_id, bank_account_id, tipo, stato, riferimento_interno,
             data_esecuzione_richiesta, importo_totale, numero_disposizioni, valuta,
             priorita, note, creato_da_user_id, created_at, updated_at)
        SELECT
            'a0000001-0000-0000-0000-000000000001'::uuid,
            c.id,
            (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1),
            'sepa_credit_transfer'::payment_order_type,
            'bozza'::payment_order_status,
            'PAG-2026-00001',
            '{today + timedelta(days=5)}'::date,
            4300.50, 3, 'EUR',
            'normale'::payment_priority,
            'Pagamento fornitori febbraio',
            u.id, NOW(), NOW()
        FROM companies c
        CROSS JOIN LATERAL (SELECT id FROM users LIMIT 1) u
        LIMIT 1
    """)

    # Righe per il SEPA CT bozza (solo se l'ordine esiste)
    op.execute("""
        INSERT INTO payment_order_lines
            (id, payment_order_id, beneficiario_nome, beneficiario_iban, importo, valuta,
             causale, end_to_end_id, stato, created_at, updated_at)
        SELECT gen_random_uuid(), po.id, v.nome, v.iban, v.importo, 'EUR',
               v.causale, v.e2e, v.stato::payment_line_status, NOW(), NOW()
        FROM payment_orders po
        CROSS JOIN (VALUES
            ('Fornitore Alpha SRL', 'IT60X0542811101000000111111', 2500.00,
             'Saldo fattura FT-2026/001', 'E2E-2026-001', 'inclusa'),
            ('Fornitore Beta SpA', 'IT60X0542811101000000222222', 1800.50,
             'Saldo fattura FT-2026/002', 'E2E-2026-002', 'inclusa'),
            ('Fornitore Extra SNC', 'DE89370400440532013000', 0.00,
             'Test riga esclusa', 'E2E-2026-003', 'esclusa')
        ) AS v(nome, iban, importo, causale, e2e, stato)
        WHERE po.id = 'a0000001-0000-0000-0000-000000000001'::uuid
    """)

    # RiBa approvata con 2 righe
    op.execute(f"""
        INSERT INTO payment_orders
            (id, company_id, bank_account_id, tipo, stato, riferimento_interno,
             data_esecuzione_richiesta, importo_totale, numero_disposizioni, valuta,
             priorita, note, creato_da_user_id, created_at, updated_at)
        SELECT
            'a0000002-0000-0000-0000-000000000002'::uuid,
            c.id,
            (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1),
            'riba'::payment_order_type,
            'approvata'::payment_order_status,
            'PAG-2026-00002',
            '{today + timedelta(days=10)}'::date,
            6200.00, 2, 'EUR',
            'alta'::payment_priority,
            'Incasso RiBa febbraio',
            u.id, NOW(), NOW()
        FROM companies c
        CROSS JOIN LATERAL (SELECT id FROM users LIMIT 1) u
        LIMIT 1
    """)

    # Righe per la RiBa approvata (solo se l'ordine esiste)
    op.execute(f"""
        INSERT INTO payment_order_lines
            (id, payment_order_id, beneficiario_nome, beneficiario_iban, importo, valuta,
             causale, stato, riba_numero_ricevuta, riba_data_scadenza, riba_piazza,
             created_at, updated_at)
        SELECT gen_random_uuid(), po.id, v.nome, v.iban, v.importo, 'EUR',
               v.causale, v.stato::payment_line_status,
               v.ricevuta, '{today + timedelta(days=10)}'::date, v.piazza, NOW(), NOW()
        FROM payment_orders po
        CROSS JOIN (VALUES
            ('Cliente Gamma SRL', 'IT60X0542811101000000333333', 4200.00,
             'RiBa FV-2026/001', 'inclusa', '001', 'Milano'),
            ('Cliente Delta SpA', 'IT60X0542811101000000444444', 2000.00,
             'RiBa FV-2026/002', 'inclusa', '002', 'Roma')
        ) AS v(nome, iban, importo, causale, stato, ricevuta, piazza)
        WHERE po.id = 'a0000002-0000-0000-0000-000000000002'::uuid
    """)

    # SEPA CT eseguita con 1 riga
    op.execute(f"""
        INSERT INTO payment_orders
            (id, company_id, bank_account_id, tipo, stato, riferimento_interno,
             data_esecuzione_richiesta, importo_totale, numero_disposizioni, valuta,
             priorita, note, creato_da_user_id, created_at, updated_at)
        SELECT
            'a0000003-0000-0000-0000-000000000003'::uuid,
            c.id,
            (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1),
            'sepa_credit_transfer'::payment_order_type,
            'eseguita'::payment_order_status,
            'PAG-2026-00003',
            '{today - timedelta(days=3)}'::date,
            1500.00, 1, 'EUR',
            'normale'::payment_priority,
            'Pagamento completato',
            u.id, NOW(), NOW()
        FROM companies c
        CROSS JOIN LATERAL (SELECT id FROM users LIMIT 1) u
        LIMIT 1
    """)

    # Riga per SEPA CT eseguita (solo se l'ordine esiste)
    op.execute("""
        INSERT INTO payment_order_lines
            (id, payment_order_id, beneficiario_nome, beneficiario_iban, importo, valuta,
             causale, end_to_end_id, stato, created_at, updated_at)
        SELECT gen_random_uuid(), po.id,
               'Fornitore Iota SAS', 'IT60X0542811101000000555555', 1500.00, 'EUR',
               'Saldo fattura ND-2026/001', 'E2E-2026-004', 'eseguita'::payment_line_status,
               NOW(), NOW()
        FROM payment_orders po
        WHERE po.id = 'a0000003-0000-0000-0000-000000000003'::uuid
    """)

    # 1 Template SEPA (bank_account_id nullable)
    op.execute("""
        INSERT INTO payment_templates
            (id, company_id, nome, tipo, bank_account_id, dati_template,
             volte_utilizzato, created_at, updated_at)
        SELECT
            gen_random_uuid(), c.id,
            'Bonifico fornitori standard', 'sepa_credit_transfer'::payment_order_type,
            (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1),
            '{"priorita": "normale", "valuta": "EUR", "note_default": "Pagamento fornitore"}'::jsonb,
            3, NOW(), NOW()
        FROM companies c
        LIMIT 1
    """)


def downgrade() -> None:
    """Drop payment module tables and enums."""
    op.drop_table("payment_templates")
    op.drop_table("payment_approvals")
    op.drop_table("payment_order_lines")
    op.drop_table("payment_orders")

    sa.Enum(name="f24_section_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sdd_sequence_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sdd_mandate_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="approval_action").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_line_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_order_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_order_type").drop(op.get_bind(), checkfirst=True)
