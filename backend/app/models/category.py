import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_category_company_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6b7280")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="categories")  # noqa: F821
    subcategories: Mapped[list["Subcategory"]] = relationship(  # noqa: F821
        back_populates="category", lazy="selectin", cascade="all, delete-orphan"
    )
