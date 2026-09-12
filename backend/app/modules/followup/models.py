from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # Production Check: Interaction connection with cascade deletion and indexing
    interaction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Fast lookup for interaction history
    )

    # Production Check: NEW COLUMN - Kisko ye task assigned hai (Sales Rep Mapping)
    assigned_to: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Sales rep dashboard queries super fast karega
    )

    # Task deadline details
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Production Check: Defined length and index for dashboard filters (Pending/Completed)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Automated server-side audit logs
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Production Check: NEW COLUMN - Automated tracking for task state changes
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
