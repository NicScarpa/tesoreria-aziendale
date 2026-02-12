import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    tax_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="IT", nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    fiscal_regime: Mapped[str | None] = mapped_column(String(10), nullable=True)
    group_vat_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    province_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    certified_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_companies: Mapped[list["UserCompany"]] = relationship(  # noqa: F821
        back_populates="company", lazy="selectin"
    )
    bank_connections: Mapped[list["BankConnection"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    bank_accounts: Mapped[list["BankAccount"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    reconciliation_rules: Mapped[list["ReconciliationRule"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    notification_preferences: Mapped[list["NotificationPreference"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    categories: Mapped[list["Category"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    subcategories: Mapped[list["Subcategory"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    categorization_rules: Mapped[list["CategorizationRule"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    import_batches: Mapped[list["ImportBatch"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    expected_transactions: Mapped[list["ExpectedTransaction"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    reconciliations: Mapped[list["Reconciliation"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    payment_orders: Mapped[list["PaymentOrder"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    payment_templates: Mapped[list["PaymentTemplate"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    cash_flow_forecasts: Mapped[list["CashFlowForecast"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    open_banking_connections: Mapped[list["OpenBankingConnection"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    invoice_imports: Mapped[list["InvoiceImport"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    invoice_import_batches: Mapped[list["InvoiceImportBatch"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    integration_configs: Mapped[list["IntegrationConfig"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
    webhook_endpoints: Mapped[list["WebhookEndpoint"]] = relationship(back_populates="company", lazy="select")  # noqa: F821
