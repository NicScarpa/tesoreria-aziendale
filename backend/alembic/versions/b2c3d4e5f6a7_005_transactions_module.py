"""005_transactions_module

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create transactions module tables and enums."""
    # ENUM operations must be outside transaction
    op.execute("COMMIT")

    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE flow_direction AS ENUM ('inflow', 'outflow');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE transaction_status AS ENUM ('pending', 'booked', 'rejected');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE transaction_type AS ENUM ('credit_transfer', 'direct_debit', 'card_payment', 'cash', 'fee', 'interest', 'tax', 'other');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE categorization_source AS ENUM ('manual', 'automatic', 'rule', 'import');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE rule_action_type AS ENUM ('set_category');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            CREATE TYPE batch_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'partial');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("BEGIN")

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6b7280"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "name", name="uq_category_company_name"),
    )
    op.create_index(op.f("ix_categories_company_id"), "categories", ["company_id"])

    # --- subcategories ---
    op.create_table(
        "subcategories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "name", name="uq_subcategory_category_name"),
    )
    op.create_index(op.f("ix_subcategories_category_id"), "subcategories", ["category_id"])
    op.create_index(op.f("ix_subcategories_company_id"), "subcategories", ["company_id"])

    # --- import_batches (must exist before transactions FK) ---
    op.create_table(
        "import_batches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "processing", "completed", "failed", "partial",
                            name="batch_status", create_type=False),
            nullable=False, server_default="pending",
        ),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_batches_company_id"), "import_batches", ["company_id"])

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("bank_account_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column(
            "direction",
            postgresql.ENUM("inflow", "outflow", name="flow_direction", create_type=False),
            nullable=False,
        ),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("remittance_info", sa.Text(), nullable=True),
        sa.Column(
            "transaction_type",
            postgresql.ENUM("credit_transfer", "direct_debit", "card_payment", "cash",
                            "fee", "interest", "tax", "other",
                            name="transaction_type", create_type=False),
            nullable=False, server_default="other",
        ),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("subcategory_id", sa.UUID(), nullable=True),
        sa.Column(
            "categorization_source",
            postgresql.ENUM("manual", "automatic", "rule", "import",
                            name="categorization_source", create_type=False),
            nullable=True,
        ),
        sa.Column("counterpart_id", sa.UUID(), nullable=True),
        sa.Column("counterpart_name", sa.String(255), nullable=True),
        sa.Column("counterpart_iban", sa.String(34), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "booked", "rejected",
                            name="transaction_status", create_type=False),
            nullable=False, server_default="booked",
        ),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("provider_transaction_id", sa.String(255), nullable=True),
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column("import_batch_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subcategory_id"], ["subcategories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_company_id"), "transactions", ["company_id"])
    op.create_index(op.f("ix_transactions_bank_account_id"), "transactions", ["bank_account_id"])
    op.create_index(op.f("ix_transactions_transaction_date"), "transactions", ["transaction_date"])
    op.create_index(op.f("ix_transactions_category_id"), "transactions", ["category_id"])
    op.create_index(op.f("ix_transactions_subcategory_id"), "transactions", ["subcategory_id"])
    op.create_index(op.f("ix_transactions_counterpart_id"), "transactions", ["counterpart_id"])
    op.create_index(op.f("ix_transactions_status"), "transactions", ["status"])

    # Compound index for main query
    op.execute("""
        CREATE INDEX idx_transactions_main ON transactions(company_id, transaction_date DESC)
        WHERE hidden_at IS NULL;
    """)

    # Provider dedup partial unique index
    op.execute("""
        CREATE UNIQUE INDEX idx_transactions_provider_dedup
        ON transactions(bank_account_id, provider_transaction_id)
        WHERE provider_transaction_id IS NOT NULL;
    """)

    # Full-text search GIN index (Italian)
    op.execute("""
        CREATE INDEX idx_transactions_fts ON transactions
        USING gin(to_tsvector('italian', COALESCE(description,'') || ' ' || COALESCE(remittance_info,'') || ' ' || COALESCE(notes,'')));
    """)

    # --- transaction_allocations ---
    op.create_table(
        "transaction_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("transaction_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("subcategory_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subcategory_id"], ["subcategories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transaction_allocations_transaction_id"), "transaction_allocations", ["transaction_id"])

    # --- categorization_rules ---
    op.create_table(
        "categorization_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column(
            "direction",
            postgresql.ENUM("inflow", "outflow", name="flow_direction", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "action_type",
            postgresql.ENUM("set_category", name="rule_action_type", create_type=False),
            nullable=False, server_default="set_category",
        ),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("subcategory_id", sa.UUID(), nullable=True),
        sa.Column("conditions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subcategory_id"], ["subcategories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categorization_rules_company_id"), "categorization_rules", ["company_id"])


def downgrade() -> None:
    """Drop transactions module tables and enums."""
    op.drop_table("categorization_rules")
    op.drop_table("transaction_allocations")
    op.execute("DROP INDEX IF EXISTS idx_transactions_fts")
    op.execute("DROP INDEX IF EXISTS idx_transactions_provider_dedup")
    op.execute("DROP INDEX IF EXISTS idx_transactions_main")
    op.drop_table("transactions")
    op.drop_table("import_batches")
    op.drop_table("subcategories")
    op.drop_table("categories")

    sa.Enum(name="batch_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="rule_action_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="categorization_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transaction_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transaction_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="flow_direction").drop(op.get_bind(), checkfirst=True)
