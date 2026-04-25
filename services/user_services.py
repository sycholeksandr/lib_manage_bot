from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from db.repositories.user_repository import get_user_by_id, create_user
from db.repositories.user_repository import set_user_admin_status 

async def create_user_or_get_existing(
    session: AsyncSession,
    user_id: int,
    full_name: str,
    contact: str,
    is_admin: bool = False,
    tg_username: str | None = None,
) -> User:
    existing_user = await get_user_by_id(session, user_id)

    if existing_user is not None:
        return existing_user
    # await create_log_entry(session, "create_user", user_id, None, None, full_name)
    return await create_user(session, user_id, full_name, contact, is_admin, tg_username)

async def set_user_admin_status_service(
    session: AsyncSession,
    user_id: int,
    is_admin: bool
) -> bool:
    return await set_user_admin_status(session, user_id, is_admin)

async def get_user_by_id_service(
    session: AsyncSession,
    user_id: int
) -> User | None:
    return await get_user_by_id(session, user_id)

async def update_user_tg_username_service(
    session: AsyncSession,
    user_id: int,
    tg_username: str
) -> bool:
    user = await get_user_by_id(session, user_id)

    if user is None:
        return False

    user.tg_username = tg_username
    # await create_log_entry(session, "update_user_tg_username", user_id, None, None, user.full_name)
    await session.commit()
    return True