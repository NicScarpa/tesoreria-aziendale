import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, UniqueConstraint, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, UserCompanyStatus



class UserCompany(Base):
    __tablename__ = "user_companies"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.VIEWER,
    )
    status: Mapped[UserCompanyStatus] = mapped_column(
        Enum(UserCompanyStatus, name="user_company_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserCompanyStatus.ACTIVE,
    )
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="user_companies", foreign_keys=[user_id])  # noqa: F821
    company: Mapped["Company"] = relationship(back_populates="user_companies")  # noqa: F821
