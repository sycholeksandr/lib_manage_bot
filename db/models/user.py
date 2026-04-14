from datetime import datetime, UTC

from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    contact: Mapped[str] = mapped_column(Text, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tg_username: Mapped[str] = mapped_column(Text, nullable=True)
