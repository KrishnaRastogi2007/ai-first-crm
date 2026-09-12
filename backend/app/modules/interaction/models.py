from sqlalchemy import DateTime,String,Integer  , func , ForeignKey , Text
from datetime import datetime
from sqlalchemy.orm import Mapped , mapped_column
from app.db.base import Base
class Interaction(Base):
    __tablename__ = "interactions"

    id:Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    hcp_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hcps.id" , ondelete="CASCADE"),
        nullable= False,
        index=True
    )

    user_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id" ,ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    interaction_type:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    subject:Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    notes:Mapped[str | None] = mapped_column(
        Text,
        nullable=True

    )

    interaction_date:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now()
)