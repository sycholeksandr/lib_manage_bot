from datetime import datetime, UTC

from sqlalchemy import BigInteger, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

class Logger(Base):
    __tablename__ = "logger"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    action: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True)
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("book.id", ondelete="SET NULL"),
         nullable=True)
    user_full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    book_title: Mapped[str | None] = mapped_column(Text, nullable=True)