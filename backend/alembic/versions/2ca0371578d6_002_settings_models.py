"""002_settings_models

Revision ID: 2ca0371578d6
Revises: c6821703a042
Create Date: 2026-02-11 08:14:32.479239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2ca0371578d6'
down_revision: Union[str, Sequence[str], None] = 'c6821703a042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Extend existing enums with new values ---
    # NOTE: ALTER TYPE ... ADD VALUE cannot run inside a transaction in PostgreSQL.
    # We must execute these outside the current transaction block.
    op.execute("COMMIT")
    op.execute("ALTER TYPE user_company_status ADD VALUE IF NOT EXISTS 'removed'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'role_changed'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'user_invited'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'user_removed'")
    op.execute("BEGIN")

    # --- New tables ---
    op.create_table('institutions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=500), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('country', sa.String(length=2), nullable=False),
    sa.Column('bic', sa.String(length=11), nullable=True),
    sa.Column('hidden', sa.Boolean(), nullable=False),
    sa.Column('icon_url', sa.String(length=500), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_institutions_bic'), 'institutions', ['bic'], unique=False)

    op.create_table('bank_connections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'REVOKED', 'PENDING', name='consent_status', create_constraint=True), nullable=False),
    sa.Column('purpose', sa.Enum('AISP', 'PISP', 'BOTH', name='consent_purpose', create_constraint=True), nullable=False),
    sa.Column('provider_source_id', sa.String(length=255), nullable=True),
    sa.Column('authorized_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('next_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_connections_company_id'), 'bank_connections', ['company_id'], unique=False)

    op.create_table('notification_preferences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('notification_type', sa.Enum('LOW_BALANCE', 'CRITICAL_BALANCE', 'SYNC_COMPLETE', 'SYNC_ERROR', 'RECONCILIATION_COMPLETE', 'PAYMENT_DUE', 'USER_INVITED', 'ROLE_CHANGED', name='notification_type', create_constraint=True), nullable=False),
    sa.Column('in_app', sa.Boolean(), nullable=False),
    sa.Column('email', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'company_id', 'notification_type', name='uq_notification_pref')
    )
    op.create_index(op.f('ix_notification_preferences_company_id'), 'notification_preferences', ['company_id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)

    op.create_table('reconciliation_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('match_amount', sa.Boolean(), nullable=False),
    sa.Column('amount_tolerance', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('match_date', sa.Boolean(), nullable=False),
    sa.Column('date_tolerance_days', sa.Integer(), nullable=False),
    sa.Column('match_description', sa.Boolean(), nullable=False),
    sa.Column('match_counterpart', sa.Boolean(), nullable=False),
    sa.Column('auto_confirm', sa.Boolean(), nullable=False),
    sa.Column('min_confidence', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_rules_company_id'), 'reconciliation_rules', ['company_id'], unique=False)

    op.create_table('bank_accounts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('bank_connection_id', sa.UUID(), nullable=False),
    sa.Column('nickname', sa.String(length=255), nullable=True),
    sa.Column('iban', sa.String(length=34), nullable=True),
    sa.Column('bic', sa.String(length=11), nullable=True),
    sa.Column('account_number', sa.String(length=50), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('available_balance', sa.Numeric(precision=15, scale=2), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'CLOSED', 'BLOCKED', name='account_status', create_constraint=True), nullable=False),
    sa.Column('ignore_balance', sa.Boolean(), nullable=False),
    sa.Column('hidden_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['bank_connection_id'], ['bank_connections.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_accounts_company_id'), 'bank_accounts', ['company_id'], unique=False)
    op.create_index(op.f('ix_bank_accounts_iban'), 'bank_accounts', ['iban'], unique=False)

    # --- Alter existing tables ---
    op.add_column('companies', sa.Column('fiscal_regime', sa.String(length=10), nullable=True))
    op.add_column('companies', sa.Column('group_vat_number', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('postal_code', sa.String(length=10), nullable=True))
    op.add_column('companies', sa.Column('province_code', sa.String(length=5), nullable=True))
    op.add_column('companies', sa.Column('certified_email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('destination_code', sa.String(length=7), nullable=True))
    op.add_column('companies', sa.Column('default_currency', sa.String(length=3), server_default='EUR', nullable=False))
    op.add_column('companies', sa.Column('logo_url', sa.String(length=500), nullable=True))

    op.add_column('user_companies', sa.Column('invited_by', sa.UUID(), nullable=True))
    op.add_column('user_companies', sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_companies', sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_companies', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_user_companies_invited_by', 'user_companies', 'users',
        ['invited_by'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""

    # --- Revert user_companies changes ---
    op.drop_constraint('fk_user_companies_invited_by', 'user_companies', type_='foreignkey')
    op.drop_column('user_companies', 'updated_at')
    op.drop_column('user_companies', 'joined_at')
    op.drop_column('user_companies', 'invited_at')
    op.drop_column('user_companies', 'invited_by')

    # --- Revert companies changes ---
    op.drop_column('companies', 'logo_url')
    op.drop_column('companies', 'default_currency')
    op.drop_column('companies', 'destination_code')
    op.drop_column('companies', 'certified_email')
    op.drop_column('companies', 'province_code')
    op.drop_column('companies', 'postal_code')
    op.drop_column('companies', 'city')
    op.drop_column('companies', 'group_vat_number')
    op.drop_column('companies', 'fiscal_regime')

    # --- Drop new tables (order matters: children first) ---
    op.drop_index(op.f('ix_bank_accounts_iban'), table_name='bank_accounts')
    op.drop_index(op.f('ix_bank_accounts_company_id'), table_name='bank_accounts')
    op.drop_table('bank_accounts')

    op.drop_index(op.f('ix_reconciliation_rules_company_id'), table_name='reconciliation_rules')
    op.drop_table('reconciliation_rules')

    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_company_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')

    op.drop_index(op.f('ix_bank_connections_company_id'), table_name='bank_connections')
    op.drop_table('bank_connections')

    op.drop_index(op.f('ix_institutions_bic'), table_name='institutions')
    op.drop_table('institutions')

    # --- Drop new enum types (after tables that use them are dropped) ---
    sa.Enum(name='account_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='notification_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='consent_purpose').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='consent_status').drop(op.get_bind(), checkfirst=True)

    # --- Revert enum value additions ---
    # NOTE: PostgreSQL does not support removing values from an enum type.
    # The added values (user_company_status='removed', audit_action='role_changed',
    # 'user_invited', 'user_removed') will remain in the enum types.
    # To fully revert, you would need to recreate the enum types, which is
    # complex and risky. These extra values are harmless if not used.
