"""006_reconciliation_module

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-11 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reconciliation module tables, enums, and alter existing tables."""
    # ENUM operations must be outside transaction
    op.execute("COMMIT")

    # --- New enums ---
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE reconciliation_status AS ENUM ('unreconciled', 'partially_reconciled', 'reconciled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE expected_transaction_type AS ENUM ('expected_inflow', 'expected_outflow');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE expected_document_type AS ENUM ('sales_invoice', 'purchase_invoice', 'credit_note', 'debit_note', 'salary', 'tax', 'other');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE expected_transaction_status AS ENUM ('open', 'partially_matched', 'matched', 'cancelled', 'expired');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE expected_transaction_source AS ENUM ('manual', 'invoice_import', 'schedule', 'sdi_sync');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE reconciliation_line_type AS ENUM ('transaction_match', 'expected_match', 'adjustment');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE reconciliation_rule_match_type AS ENUM ('exact_amount', 'amount_tolerance', 'reference', 'counterpart', 'combined');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE reconciliation_rule_action AS ENUM ('auto_reconcile', 'suggest');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- expected_transactions ---
    op.create_table(
        "expected_transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=True),
        sa.Column("counterpart_name", sa.String(255), nullable=True),
        sa.Column("counterpart_iban", sa.String(34), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM("expected_inflow", "expected_outflow",
                            name="expected_transaction_type", create_type=False),
            nullable=False,
        ),
        sa.Column("expected_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_number", sa.String(255), nullable=True),
        sa.Column(
            "document_type",
            postgresql.ENUM("sales_invoice", "purchase_invoice", "credit_note", "debit_note",
                            "salary", "tax", "other",
                            name="expected_document_type", create_type=False),
            nullable=False, server_default="other",
        ),
        sa.Column(
            "status",
            postgresql.ENUM("open", "partially_matched", "matched", "cancelled", "expired",
                            name="expected_transaction_status", create_type=False),
            nullable=False, server_default="open",
        ),
        sa.Column("matched_amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("schedule_id", sa.UUID(), nullable=True),
        sa.Column(
            "source",
            postgresql.ENUM("manual", "invoice_import", "schedule", "sdi_sync",
                            name="expected_transaction_source", create_type=False),
            nullable=False, server_default="manual",
        ),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expected_transactions_company_id"), "expected_transactions", ["company_id"])
    op.create_index(op.f("ix_expected_transactions_bank_account_id"), "expected_transactions", ["bank_account_id"])
    op.create_index(op.f("ix_expected_transactions_due_date"), "expected_transactions", ["due_date"])
    op.create_index(op.f("ix_expected_transactions_status"), "expected_transactions", ["status"])
    op.create_index("ix_expected_transactions_company_status_due", "expected_transactions",
                    ["company_id", "status", "due_date"])
    op.create_index("ix_expected_transactions_company_type_status", "expected_transactions",
                    ["company_id", "type", "status"])
    op.create_index("ix_expected_transactions_ref_company", "expected_transactions",
                    ["reference_number", "company_id"])

    # --- reconciliations ---
    op.create_table(
        "reconciliations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("reconciliation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_by_user_id", sa.UUID(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("matching_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("applied_rule", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["confirmed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reconciliations_company_id"), "reconciliations", ["company_id"])
    op.create_index(op.f("ix_reconciliations_status"), "reconciliations", ["status"])
    op.create_index("ix_reconciliations_company_status", "reconciliations", ["company_id", "status"])
    op.create_index("ix_reconciliations_company_date", "reconciliations", ["company_id", "reconciliation_date"])

    # --- reconciliation_lines ---
    op.create_table(
        "reconciliation_lines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reconciliation_id", sa.UUID(), nullable=False),
        sa.Column("transaction_id", sa.UUID(), nullable=True),
        sa.Column("expected_transaction_id", sa.UUID(), nullable=True),
        sa.Column("matched_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "line_type",
            postgresql.ENUM("transaction_match", "expected_match", "adjustment",
                            name="reconciliation_line_type", create_type=False),
            nullable=False, server_default="transaction_match",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reconciliation_id"], ["reconciliations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["expected_transaction_id"], ["expected_transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "transaction_id IS NOT NULL OR expected_transaction_id IS NOT NULL",
            name="ck_reconciliation_line_has_ref",
        ),
    )
    op.create_index(op.f("ix_reconciliation_lines_reconciliation_id"), "reconciliation_lines", ["reconciliation_id"])
    op.create_index(op.f("ix_reconciliation_lines_transaction_id"), "reconciliation_lines", ["transaction_id"])
    op.create_index(op.f("ix_reconciliation_lines_expected_transaction_id"), "reconciliation_lines",
                    ["expected_transaction_id"])

    # --- ALTER transactions: add reconciliation_status + reconciliation_id ---
    op.add_column("transactions", sa.Column(
        "reconciliation_status",
        postgresql.ENUM("unreconciled", "partially_reconciled", "reconciled",
                        name="reconciliation_status", create_type=False),
        nullable=False, server_default="unreconciled",
    ))
    op.add_column("transactions", sa.Column(
        "reconciliation_id", sa.UUID(), nullable=True,
    ))
    op.create_foreign_key(
        "fk_transactions_reconciliation_id", "transactions", "reconciliations",
        ["reconciliation_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index(op.f("ix_transactions_reconciliation_status"), "transactions", ["reconciliation_status"])

    # --- ALTER reconciliation_rules: add new columns ---
    op.add_column("reconciliation_rules", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("reconciliation_rules", sa.Column(
        "conditions", postgresql.JSONB(), nullable=True, server_default="[]"
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "match_type",
        postgresql.ENUM("exact_amount", "amount_tolerance", "reference", "counterpart", "combined",
                        name="reconciliation_rule_match_type", create_type=False),
        nullable=False, server_default="exact_amount",
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "action",
        postgresql.ENUM("auto_reconcile", "suggest",
                        name="reconciliation_rule_action", create_type=False),
        nullable=False, server_default="suggest",
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "amount_tolerance_override", sa.Numeric(precision=15, scale=2), nullable=True
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "date_tolerance_override", sa.Integer(), nullable=True
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "reference_pattern", sa.String(255), nullable=True
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "require_same_counterpart", sa.Boolean(), nullable=False, server_default="false"
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "times_applied", sa.Integer(), nullable=False, server_default="0"
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "last_applied_at", sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column("reconciliation_rules", sa.Column(
        "confirmation_rate", sa.Numeric(precision=5, scale=2), nullable=True
    ))

    # --- Seed data ---
    _seed_data()


def _seed_data() -> None:
    """Insert seed expected transactions and default reconciliation rules."""
    from datetime import date, timedelta
    import uuid

    today = date.today()

    op.execute(f"""
        INSERT INTO expected_transactions
            (id, company_id, bank_account_id, counterpart_name, counterpart_iban,
             type, expected_amount, currency, due_date, description, reference_number,
             document_type, status, matched_amount, source, metadata, created_at, updated_at)
        SELECT
            gen_random_uuid(), c.id, ba.id,
            e.counterpart_name, e.counterpart_iban,
            e.type::expected_transaction_type, e.expected_amount, 'EUR', e.due_date, e.description, e.reference_number,
            e.document_type::expected_document_type, 'open'::expected_transaction_status, 0,
            'manual'::expected_transaction_source, '{{}}'::jsonb, NOW(), NOW()
        FROM companies c
        CROSS JOIN LATERAL (SELECT id FROM bank_accounts WHERE company_id = c.id LIMIT 1) ba
        CROSS JOIN (VALUES
            ('Fornitore Alpha SRL', 'IT60X0542811101000000111111', 'expected_outflow', 2500.00,
             '{today + timedelta(days=5)}'::date, 'Fattura acquisto materiali', 'FT-2026/001', 'purchase_invoice'),
            ('Fornitore Beta SpA', 'IT60X0542811101000000222222', 'expected_outflow', 1800.50,
             '{today + timedelta(days=10)}'::date, 'Fattura servizi consulenza', 'FT-2026/002', 'purchase_invoice'),
            ('Cliente Gamma SRL', 'IT60X0542811101000000333333', 'expected_inflow', 5000.00,
             '{today + timedelta(days=3)}'::date, 'Fattura vendita prodotti', 'FV-2026/001', 'sales_invoice'),
            ('Cliente Delta SpA', 'IT60X0542811101000000444444', 'expected_inflow', 3200.00,
             '{today + timedelta(days=7)}'::date, 'Fattura vendita servizi', 'FV-2026/002', 'sales_invoice'),
            ('Fornitore Epsilon SNC', NULL, 'expected_outflow', 750.00,
             '{today + timedelta(days=15)}'::date, 'Nota credito fornitore', 'NC-2026/001', 'credit_note'),
            ('Dipendenti', NULL, 'expected_outflow', 4500.00,
             '{today + timedelta(days=1)}'::date, 'Stipendi febbraio 2026', NULL, 'salary'),
            ('Agenzia Entrate', NULL, 'expected_outflow', 1200.00,
             '{today + timedelta(days=16)}'::date, 'F24 IVA gennaio', 'F24-2026/01', 'tax'),
            ('Cliente Zeta SRL', 'IT60X0542811101000000555555', 'expected_inflow', 980.00,
             '{today - timedelta(days=2)}'::date, 'Fattura vendita scaduta', 'FV-2026/003', 'sales_invoice'),
            ('Fornitore Eta SRL', 'IT60X0542811101000000666666', 'expected_outflow', 3100.00,
             '{today + timedelta(days=20)}'::date, 'Fattura acquisto macchinari', 'FT-2026/003', 'purchase_invoice'),
            ('Cliente Theta SpA', 'IT60X0542811101000000777777', 'expected_inflow', 7500.00,
             '{today + timedelta(days=30)}'::date, 'Fattura vendita progetto', 'FV-2026/004', 'sales_invoice'),
            ('Fornitore Iota SAS', NULL, 'expected_outflow', 450.00,
             '{today + timedelta(days=8)}'::date, 'Nota debito spese spedizione', 'ND-2026/001', 'debit_note'),
            ('Utilities SpA', NULL, 'expected_outflow', 320.00,
             '{today + timedelta(days=12)}'::date, 'Bolletta energia elettrica', NULL, 'other')
        ) AS e(counterpart_name, counterpart_iban, type, expected_amount, due_date, description, reference_number, document_type)
        WHERE EXISTS (SELECT 1 FROM bank_accounts WHERE company_id = c.id)
    """)

    op.execute("""
        INSERT INTO reconciliation_rules
            (id, company_id, name, description, match_amount, amount_tolerance,
             match_date, date_tolerance_days, match_description, match_counterpart,
             auto_confirm, min_confidence, priority, is_active,
             match_type, action, require_same_counterpart,
             times_applied, created_at, updated_at)
        SELECT
            gen_random_uuid(), c.id,
            r.name, r.description, r.match_amount, r.amount_tolerance,
            r.match_date, r.date_tolerance_days, r.match_description, r.match_counterpart,
            r.auto_confirm, r.min_confidence, r.priority, true,
            r.match_type::reconciliation_rule_match_type,
            r.action::reconciliation_rule_action,
            r.require_same_counterpart,
            0, NOW(), NOW()
        FROM companies c
        CROSS JOIN (VALUES
            ('Matching Esatto', 'Importo esatto + stessa controparte + riferimento in descrizione',
             true, 0.01, true, 3, true, true, false, 0.95, 100, 'exact_amount', 'auto_reconcile', true),
            ('Matching Tollerante', 'Importo entro tolleranza + stessa controparte',
             true, 5.00, true, 5, false, true, false, 0.70, 50, 'amount_tolerance', 'suggest', true),
            ('Solo Importo', 'Match solo su importo esatto, qualsiasi controparte',
             true, 0.01, false, 0, false, false, false, 0.50, 10, 'exact_amount', 'suggest', false)
        ) AS r(name, description, match_amount, amount_tolerance, match_date, date_tolerance_days,
               match_description, match_counterpart, auto_confirm, min_confidence, priority,
               match_type, action, require_same_counterpart)
    """)


def downgrade() -> None:
    """Drop reconciliation module tables and columns."""
    # --- Remove altered columns from reconciliation_rules ---
    op.drop_column("reconciliation_rules", "confirmation_rate")
    op.drop_column("reconciliation_rules", "last_applied_at")
    op.drop_column("reconciliation_rules", "times_applied")
    op.drop_column("reconciliation_rules", "require_same_counterpart")
    op.drop_column("reconciliation_rules", "reference_pattern")
    op.drop_column("reconciliation_rules", "date_tolerance_override")
    op.drop_column("reconciliation_rules", "amount_tolerance_override")
    op.drop_column("reconciliation_rules", "action")
    op.drop_column("reconciliation_rules", "match_type")
    op.drop_column("reconciliation_rules", "conditions")
    op.drop_column("reconciliation_rules", "description")

    # --- Remove altered columns from transactions ---
    op.drop_index(op.f("ix_transactions_reconciliation_status"), table_name="transactions")
    op.drop_constraint("fk_transactions_reconciliation_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "reconciliation_id")
    op.drop_column("transactions", "reconciliation_status")

    # --- Drop new tables ---
    op.drop_table("reconciliation_lines")
    op.drop_table("reconciliations")
    op.drop_table("expected_transactions")

    # --- Drop enums ---
    sa.Enum(name="reconciliation_rule_action").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reconciliation_rule_match_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reconciliation_line_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="expected_transaction_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="expected_transaction_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="expected_document_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="expected_transaction_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reconciliation_status").drop(op.get_bind(), checkfirst=True)
