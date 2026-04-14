import pytest
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from services.user_services import create_user_or_get_existing, set_user_admin_status_service

@pytest.mark.asyncio
async def test_db_connection(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1

@pytest.mark.asyncio
async def test_create_user_or_get_existing_creates_new_user(db_session, clean_db):
    user_id = 111111111
    full_name = "test_user"
    tg_username = "test_user_tg"
    contact = "test_user_contact"
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=user_id,
        full_name=full_name,
        is_admin=True,
        tg_username = tg_username,
        contact = contact
    )

    assert user is not None
    assert user.id == user_id
    assert user.full_name == full_name
    assert user.is_admin is True
    assert user.registered_at is not None
    assert user.tg_username == tg_username
    assert user.contact == contact

    stmt = select(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    saved_user = result.scalar_one_or_none()

    assert saved_user is not None
    assert saved_user.id == user_id
    assert saved_user.full_name == full_name
    assert saved_user.is_admin is True
    assert saved_user.registered_at is not None
    assert saved_user.tg_username == tg_username
    assert saved_user.contact == contact


@pytest.mark.asyncio
async def test_create_user_or_get_existing_returns_existing_user(db_session, clean_db):
    user_id = 222222222
    full_name = "existing_user"
    tg_username = "existing_user_tg"
    contact = "existing_user_contact"

    first_user = await create_user_or_get_existing(
        session=db_session,
        user_id=user_id,
        full_name=full_name,
        is_admin=False,
        tg_username=tg_username,
        contact=contact
    )

    second_user = await create_user_or_get_existing(
        session=db_session,
        user_id=user_id,
        full_name="new_name_should_not_replace_old_one",
        is_admin=True,
        tg_username=tg_username,
        contact=contact
    )

    assert first_user is not None
    assert second_user is not None

    assert first_user.id == second_user.id
    assert second_user.id == user_id

    stmt = select(func.count()).select_from(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    users_count = result.scalar_one()

    assert users_count == 1

    stmt = select(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    saved_user = result.scalar_one()

    assert saved_user.full_name == full_name
    assert saved_user.is_admin is False
    assert saved_user.tg_username == "existing_user_tg"
    assert saved_user.contact == "existing_user_contact"

@pytest.mark.asyncio
async def test_set_user_admin_status(db_session, clean_db):
    user_id = 333333333
    full_name = "admin_status_user"
    tg_username  = "admin_status_user_tg"
    contact = "admin_status_user_contact"

    user = await create_user_or_get_existing(
        session=db_session,
        user_id=user_id,
        full_name=full_name,
        is_admin=False,
        tg_username=tg_username,
        contact=contact
    )

    assert user.is_admin is False

    result = await set_user_admin_status_service(db_session, user_id, True)
    assert result is not False

    stmt = select(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    updated_user = result.scalar_one()

    assert updated_user.is_admin is True