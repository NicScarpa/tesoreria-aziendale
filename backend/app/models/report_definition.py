import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReportFormat, ReportType


class ReportDefinition(Base):
    __tablename__ = "report_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    formato_default: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReportFormat.PDF,
    )
    parametri_default: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    layout: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_preferito: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    executions: Mapped[list["ReportExecution"]] = relationship(back_populates="report_definition")  # noqa: F821
    schedules: Mapped[list["ReportSchedule"]] = relationship(back_populates="report_definition")  # noqa: F821

    __table_args__ = (
        Index("ix_report_definitions_company_tipo", "company_id", "tipo"),
        Index("ix_report_definitions_company_preferito", "company_id", "is_preferito"),
        Index("ix_report_definitions_company_system", "company_id", "is_system"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # SQLAlchemy column defaults are applied at INSERT time; tests expect
        # Python-level defaults on newly created objects.
        if self.formato_default is None:
            self.formato_default = ReportFormat.PDF
        if self.parametri_default is None:
            self.parametri_default = {}
        if self.layout is None:
            self.layout = {}
        if self.is_system is None:
            self.is_system = False
        if self.is_preferito is None:
            self.is_preferito = False
        if self.sort_order is None:
            self.sort_order = 0
