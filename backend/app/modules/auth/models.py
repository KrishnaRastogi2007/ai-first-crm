from sqlalchemy import String , Integer , Boolean , DateTime , func
from sqlalchemy.orm import Mapped , mapped_column
from app.db.base import Base
from datetime import datetime

class Users(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(
        Integer,
        primary_key = True
    )

    name:Mapped[str] = mapped_column(
        String(100),
        nullable= False
    )

    email:Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique= True,
        index= True
    )
    password_hash:Mapped[str] = mapped_column(
        String(300),
        nullable =False
    )

    role:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default= "sales_representative"
    )

    created_at:Mapped[datetime]= mapped_column(
        DateTime(timezone = True),
        server_default=func.now(),
        nullable=False

    )
    updated_at:Mapped[datetime] = mapped_column(
        DateTime(timezone =True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default= True,
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
    String(20),
    nullable=True
)