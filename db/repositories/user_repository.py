from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User

async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    contact: str,
    is_admin: bool = False,
    tg_username: str | None = None,

) -> User:
    new_user = User(
        id=user_id,
        full_name=full_name,
        contact=contact,
        is_admin=is_admin,
        tg_username=tg_username,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user

async def set_user_admin_status(session: AsyncSession, user_id: int, is_admin: bool) -> bool:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        return False

    user.is_admin = is_admin
    await session.commit()
    return user