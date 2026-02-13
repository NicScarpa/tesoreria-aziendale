import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReportFormat, ReportFrequency


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    creato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    frequenza: Mapped[ReportFrequency] = mapped_column(
        Enum(ReportFrequency, name="report_frequency",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    formato: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReportFormat.PDF,
    )
    parametri: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prossima_esecuzione: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ultima_esecuzione: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship()  # noqa: F821
    report_definition: Mapped["ReportDefinition"] = relationship(back_populates="schedules")  # noqa: F821
    creato_da: Mapped["User"] = relationship()  # noqa: F821

    __table_args__ = (
        Index("ix_report_schedules_company_attivo", "company_id", "attivo"),
        Index("ix_report_schedules_prossima_attivo", "prossima_esecuzione", "attivo"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.formato is None:
            self.formato = ReportFormat.PDF
        if self.parametri is None:
            self.parametri = {}
        if self.attivo is None:
            self.attivo = True
