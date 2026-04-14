from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.logger import Logger

async def create_log_entry(
    session: AsyncSession,
    user_id: int,
    book_id: int,
    action: str,
) -> Logger:
    new_log_entry = Logger(
        user_id=user_id,
        book_id=book_id,
        action=action,
        timestamp=datetime.now(UTC)
    )

    session.add(new_log_entry)
    await session.commit()
    await session.refresh(new_log_entry)

    return new_log_entry