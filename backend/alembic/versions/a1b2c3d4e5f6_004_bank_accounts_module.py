"""004_bank_accounts_module

Revision ID: a1b2c3d4e5f6
Revises: 983fcee2ce88
Create Date: 2026-02-11 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '983fcee2ce88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Step 1: Fix existing enum values and add new values ---
    # Must be outside transaction for ADD VALUE / RENAME VALUE
    op.execute("COMMIT")

    # Fix UPPERCASE → lowercase for account_status.
    # We recreate the type to have clean lowercase values.
    # Since bank_accounts table may have no data, and the column uses this enum,
    # we use a conditional approach: add lowercase if missing, then drop uppercase.
    #
    # Strategy: Recreate enum types with correct lowercase values.
    # PostgreSQL doesn't allow removing values, so we recreate the type.

    # --- account_status: recreate with lowercase values ---
    op.execute("""
        DO $$
        BEGIN
            -- Only rename if uppercase values still exist
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ACTIVE'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'account_status')) THEN
                -- Create a new temporary type
                CREATE TYPE account_status_new AS ENUM ('active', 'inactive', 'hidden', 'closed', 'blocked');
                -- Alter the column to use text temporarily
                ALTER TABLE bank_accounts ALTER COLUMN status TYPE text USING lower(status::text);
                -- Drop old type
                DROP TYPE account_status;
                -- Rename new type
                ALTER TYPE account_status_new RENAME TO account_status;
                -- Alter column back to enum
                ALTER TABLE bank_accounts ALTER COLUMN status TYPE account_status USING status::account_status;
            END IF;
        END $$;
    """)

    # --- consent_status: recreate with lowercase values ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ACTIVE'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'consent_status')) THEN
                CREATE TYPE consent_status_new AS ENUM ('active', 'authorized', 'expired', 'revoked', 'pending', 'disabled', 'error');
                ALTER TABLE bank_connections ALTER COLUMN status TYPE text USING lower(status::text);
                DROP TYPE consent_status;
                ALTER TYPE consent_status_new RENAME TO consent_status;
                ALTER TABLE bank_connections ALTER COLUMN status TYPE consent_status USING status::consent_status;
            ELSE
                -- Just add values if not already present
                BEGIN ALTER TYPE consent_status ADD VALUE IF NOT EXISTS 'authorized'; EXCEPTION WHEN OTHERS THEN NULL; END;
                BEGIN ALTER TYPE consent_status ADD VALUE IF NOT EXISTS 'disabled'; EXCEPTION WHEN OTHERS THEN NULL; END;
                BEGIN ALTER TYPE consent_status ADD VALUE IF NOT EXISTS 'error'; EXCEPTION WHEN OTHERS THEN NULL; END;
            END IF;
        END $$;
    """)

    # Ensure new enum types exist (may already exist from a partial previous run)
    op.execute("DO $$ BEGIN CREATE TYPE account_type AS ENUM ('checking', 'savings', 'cash', 'credit_card', 'loan', 'other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE balance_source AS ENUM ('manual', 'open_banking', 'import', 'calculated'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE access_level AS ENUM ('read', 'write', 'admin'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    # --- Normalize ALL remaining enums from UPPERCASE to lowercase ---
    # This aligns DB enum values with Python enum .value attributes (used via values_callable).

    # --- user_role ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'OWNER'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')) THEN
                CREATE TYPE user_role_new AS ENUM ('owner', 'admin', 'editor', 'viewer');
                ALTER TABLE user_companies ALTER COLUMN role TYPE text USING lower(role::text);
                DROP TYPE user_role;
                ALTER TYPE user_role_new RENAME TO user_role;
                ALTER TABLE user_companies ALTER COLUMN role TYPE user_role USING role::user_role;
            END IF;
        END $$;
    """)

    # --- user_company_status ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ACTIVE'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_company_status')) THEN
                CREATE TYPE user_company_status_new AS ENUM ('active', 'invited', 'suspended', 'removed');
                ALTER TABLE user_companies ALTER COLUMN status TYPE text USING lower(status::text);
                DROP TYPE user_company_status;
                ALTER TYPE user_company_status_new RENAME TO user_company_status;
                ALTER TABLE user_companies ALTER COLUMN status TYPE user_company_status USING status::user_company_status;
            END IF;
        END $$;
    """)

    # --- audit_action ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'LOGIN'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_action')) THEN
                CREATE TYPE audit_action_new AS ENUM ('login', 'logout', 'password_reset', 'password_change', 'user_update', 'company_update', 'user_register', 'role_changed', 'user_invited', 'user_removed');
                ALTER TABLE audit_log ALTER COLUMN action TYPE text USING lower(action::text);
                DROP TYPE audit_action;
                ALTER TYPE audit_action_new RENAME TO audit_action;
                ALTER TABLE audit_log ALTER COLUMN action TYPE audit_action USING action::audit_action;
            END IF;
        END $$;
    """)

    # --- consent_purpose ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'AISP'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'consent_purpose')) THEN
                CREATE TYPE consent_purpose_new AS ENUM ('aisp', 'pisp', 'both');
                ALTER TABLE bank_connections ALTER COLUMN purpose TYPE text USING lower(purpose::text);
                DROP TYPE consent_purpose;
                ALTER TYPE consent_purpose_new RENAME TO consent_purpose;
                ALTER TABLE bank_connections ALTER COLUMN purpose TYPE consent_purpose USING purpose::consent_purpose;
            END IF;
        END $$;
    """)

    # --- notification_type ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'LOW_BALANCE'
                       AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'notification_type')) THEN
                CREATE TYPE notification_type_new AS ENUM ('low_balance', 'critical_balance', 'sync_complete', 'sync_error', 'reconciliation_complete', 'payment_due', 'user_invited', 'role_changed');
                ALTER TABLE notification_preferences ALTER COLUMN notification_type TYPE text USING lower(notification_type::text);
                DROP TYPE notification_type;
                ALTER TYPE notification_type_new RENAME TO notification_type;
                ALTER TABLE notification_preferences ALTER COLUMN notification_type TYPE notification_type USING notification_type::notification_type;
            END IF;
        END $$;
    """)

    op.execute("BEGIN")

    # --- Step 3: ALTER TABLE bank_accounts ---

    # Make bank_connection_id nullable: drop old FK, alter column, recreate FK with SET NULL
    op.drop_constraint('bank_accounts_bank_connection_id_fkey', 'bank_accounts', type_='foreignkey')
    op.alter_column('bank_accounts', 'bank_connection_id', nullable=True)
    op.create_foreign_key(
        'bank_accounts_bank_connection_id_fkey', 'bank_accounts', 'bank_connections',
        ['bank_connection_id'], ['id'], ondelete='SET NULL'
    )

    # Add new columns
    op.add_column('bank_accounts', sa.Column('balance_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bank_accounts', sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('bank_accounts', sa.Column('allow_balance_change', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('bank_accounts', sa.Column('provider_account_id', sa.String(length=255), nullable=True))
    op.add_column('bank_accounts', sa.Column('identifiers', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('bank_accounts', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bank_accounts', sa.Column('account_type', postgresql.ENUM('checking', 'savings', 'cash', 'credit_card', 'loan', 'other', name='account_type', create_type=False), nullable=True))
    op.add_column('bank_accounts', sa.Column('color', sa.String(length=7), server_default='#6b7280', nullable=True))
    op.add_column('bank_accounts', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('bank_accounts', sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('bank_accounts', sa.Column('bank_name', sa.String(length=255), nullable=True))
    op.add_column('bank_accounts', sa.Column('bank_abi', sa.String(length=5), nullable=True))
    op.add_column('bank_accounts', sa.Column('bank_cab', sa.String(length=5), nullable=True))

    # Partial unique index for is_default
    op.execute(
        "CREATE UNIQUE INDEX idx_bank_accounts_default "
        "ON bank_accounts(company_id) "
        "WHERE is_default = TRUE AND status = 'active'"
    )

    # --- Step 4: CREATE TABLE bank_account_balances ---
    op.create_table('bank_account_balances',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('balance_date', sa.Date(), nullable=False),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('available_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('source', postgresql.ENUM('manual', 'open_banking', 'import', 'calculated', name='balance_source', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'balance_date', name='uq_bank_account_balance_date'),
    )
    op.create_index(op.f('ix_bank_account_balances_bank_account_id'), 'bank_account_balances', ['bank_account_id'], unique=False)
    op.create_index(op.f('ix_bank_account_balances_company_id'), 'bank_account_balances', ['company_id'], unique=False)

    # --- Step 5: CREATE TABLE bank_account_accesses ---
    op.create_table('bank_account_accesses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('access_level', postgresql.ENUM('read', 'write', 'admin', name='access_level', create_type=False), nullable=False),
        sa.Column('granted_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'user_id', name='uq_bank_account_user_access'),
    )
    op.create_index(op.f('ix_bank_account_accesses_bank_account_id'), 'bank_account_accesses', ['bank_account_id'], unique=False)
    op.create_index(op.f('ix_bank_account_accesses_user_id'), 'bank_account_accesses', ['user_id'], unique=False)
    op.create_index(op.f('ix_bank_account_accesses_company_id'), 'bank_account_accesses', ['company_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    # --- Drop new tables ---
    op.drop_index(op.f('ix_bank_account_accesses_company_id'), table_name='bank_account_accesses')
    op.drop_index(op.f('ix_bank_account_accesses_user_id'), table_name='bank_account_accesses')
    op.drop_index(op.f('ix_bank_account_accesses_bank_account_id'), table_name='bank_account_accesses')
    op.drop_table('bank_account_accesses')

    op.drop_index(op.f('ix_bank_account_balances_company_id'), table_name='bank_account_balances')
    op.drop_index(op.f('ix_bank_account_balances_bank_account_id'), table_name='bank_account_balances')
    op.drop_table('bank_account_balances')

    # --- Remove partial unique index ---
    op.execute("DROP INDEX IF EXISTS idx_bank_accounts_default")

    # --- Remove added columns from bank_accounts ---
    op.drop_column('bank_accounts', 'bank_cab')
    op.drop_column('bank_accounts', 'bank_abi')
    op.drop_column('bank_accounts', 'bank_name')
    op.drop_column('bank_accounts', 'is_default')
    op.drop_column('bank_accounts', 'notes')
    op.drop_column('bank_accounts', 'color')
    op.drop_column('bank_accounts', 'account_type')
    op.drop_column('bank_accounts', 'last_synced_at')
    op.drop_column('bank_accounts', 'identifiers')
    op.drop_column('bank_accounts', 'provider_account_id')
    op.drop_column('bank_accounts', 'allow_balance_change')
    op.drop_column('bank_accounts', 'credit_limit')
    op.drop_column('bank_accounts', 'balance_date')

    # --- Revert bank_connection_id to NOT NULL with CASCADE ---
    op.drop_constraint('bank_accounts_bank_connection_id_fkey', 'bank_accounts', type_='foreignkey')
    op.alter_column('bank_accounts', 'bank_connection_id', nullable=False)
    op.create_foreign_key(
        'bank_accounts_bank_connection_id_fkey', 'bank_accounts', 'bank_connections',
        ['bank_connection_id'], ['id'], ondelete='CASCADE'
    )

    # --- Drop new enum types ---
    sa.Enum(name='access_level').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='balance_source').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='account_type').drop(op.get_bind(), checkfirst=True)

    # NOTE: Cannot remove values from existing enum types (account_status, consent_status).
    # The added values (inactive, hidden, authorized, disabled, error) will remain.
