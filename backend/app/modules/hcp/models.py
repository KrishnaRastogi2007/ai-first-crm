from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HCP(Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    assigned_to: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    specialty: Mapped[str] = mapped_column(String(150), index=True, nullable=False)

    email: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    organization: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
