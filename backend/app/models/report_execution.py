import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReportExecutionStatus, ReportFormat


class ReportExecution(Base):
    __tablename__ = "report_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    generato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    formato: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    stato: Mapped[ReportExecutionStatus] = mapped_column(
        Enum(ReportExecutionStatus, name="report_execution_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReportExecutionStatus.IN_CODA,
    )
    parametri: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    risultato: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    errore: Mapped[str | None] = mapped_column(Text, nullable=True)
    righe_totali: Mapped[int | None] = mapped_column(Integer, nullable=True)

    data_generazione: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    data_completamento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_scadenza_file: Mapped[datetime | None] = mapped_column(
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
    report_definition: Mapped["ReportDefinition"] = relationship(back_populates="executions")  # noqa: F821
    generato_da: Mapped["User"] = relationship()  # noqa: F821

    __table_args__ = (
        Index("ix_report_executions_company_data", "company_id", "data_generazione"),
        Index("ix_report_executions_company_definition", "company_id", "report_definition_id"),
        Index("ix_report_executions_stato", "stato"),
        Index("ix_report_executions_scadenza", "data_scadenza_file"),
    )
