import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApprovalAction


class PaymentApproval(Base):
    __tablename__ = "payment_approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    payment_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    azione: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, name="approval_action",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    commento: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_azione: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    payment_order: Mapped["PaymentOrder"] = relationship(back_populates="approvals")  # noqa: F821
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821

    __table_args__ = (
        Index("ix_payment_approvals_order_data", "payment_order_id", "data_azione"),
    )
