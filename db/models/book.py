from datetime import datetime, UTC

from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    taken_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        )