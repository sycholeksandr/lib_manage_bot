from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.logger import Logger

async def create_log_entry(
    session: AsyncSession,
    action: str,
    user_id: int | None=None,
    book_id: int | None=None, 
    book_title: str | None = None,
    user_full_name: str | None = None
) -> Logger:
    new_log_entry = Logger(
        action=action,
        user_id=user_id,
        book_id=book_id,
        timestamp=datetime.now(UTC),
        book_title=book_title,
        user_full_name=user_full_name
    )

    session.add(new_log_entry)
    await session.commit()
    await session.refresh(new_log_entry)

    return new_log_entry