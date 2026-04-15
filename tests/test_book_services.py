import pytest

from services.book_service import (
    create_book_service,
    force_return_book_service,
    get_user_books_service,
    return_book_service,
    take_book_service,
    get_book_by_id_service,
)
from services.user_services import create_user_or_get_existing


@pytest.mark.asyncio
async def test_create_book_service_creates_book(db_session, clean_db):
    book = await create_book_service(
        session=db_session,
        title="Clean Code",
        description="A book about writing cleaner code",
    )

    assert book is not None
    assert book.id is not None
    assert book.title == "Clean Code"
    assert book.description == "A book about writing cleaner code"
    assert book.taken_by is None
    assert book.taken_at is None


@pytest.mark.asyncio
async def test_take_book_service_success(db_session, clean_db):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1001,
        full_name="reader_1",
        contact="reader_1_contact",
        tg_username="reader_1",
        is_admin=False,

    )

    book = await create_book_service(
        session=db_session,
        title="Domain-Driven Design",
        description="DDD book",
    )

    result = await take_book_service(
        session=db_session,
        user_id=user.id,
        book_id=book.id,
    )

    assert result == "success"

    updated_book = await get_book_by_id_service(db_session, book.id)
    assert updated_book is not None
    assert updated_book.taken_by == user.id
    assert updated_book.taken_at is not None


@pytest.mark.asyncio
async def test_take_book_service_returns_user_not_found(db_session, clean_db):
    book = await create_book_service(
        session=db_session,
        title="Refactoring",
        description="Martin Fowler book",
    )

    result = await take_book_service(
        session=db_session,
        user_id=999999,
        book_id=book.id,
    )

    assert result == "user_not_found"


@pytest.mark.asyncio
async def test_take_book_service_returns_book_not_found(db_session, clean_db):
    await create_user_or_get_existing(
        session=db_session,
        user_id=1002,
        full_name="reader_1",
        tg_username="reader_2",
        is_admin=False,
        contact="reader_2_contact"
    )

    result = await take_book_service(
        session=db_session,
        user_id=1002,
        book_id=999999,
    )

    assert result == "book_not_found"


@pytest.mark.asyncio
async def test_take_book_service_returns_book_already_taken(db_session, clean_db):
    first_user = await create_user_or_get_existing(
        session=db_session,
        user_id=1003,
        full_name="reader_1",
        tg_username="reader_3",
        is_admin=False,
        contact="reader_3_contact"
    )

    second_user = await create_user_or_get_existing(
        session=db_session,
        user_id=1004,
        full_name="reader_2",
        tg_username="reader_4",
        is_admin=False,
        contact="reader_4_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="The Pragmatic Programmer",
        description="Classic engineering book",
    )

    first_result = await take_book_service(
        session=db_session,
        user_id=first_user.id,
        book_id=book.id,
    )
    second_result = await take_book_service(
        session=db_session,
        user_id=second_user.id,
        book_id=book.id,
    )

    assert first_result == "success"
    assert second_result == "book_already_taken"


@pytest.mark.asyncio
async def test_return_book_service_success(db_session, clean_db):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1005,
        full_name="reader_1",
        tg_username="reader_5",
        is_admin=False,
        contact="reader_5_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Patterns of Enterprise Application Architecture",
        description="PEAA",
    )

    take_result = await take_book_service(
        session=db_session,
        user_id=user.id,
        book_id=book.id,
    )
    assert take_result == "success"

    return_result = await return_book_service(
        session=db_session,
        user_id=user.id,
        book_id=book.id,
    )

    assert return_result == "success"

    updated_book = await get_book_by_id_service(db_session, book.id)
    assert updated_book is not None
    assert updated_book.taken_by is None
    assert updated_book.taken_at is None


@pytest.mark.asyncio
async def test_return_book_service_returns_book_not_taken(db_session, clean_db):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1006,
        full_name="reader_1",
        tg_username="reader_6",
        is_admin=False,
        contact="reader_6_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Design Patterns",
        description="GoF",
    )

    result = await return_book_service(
        session=db_session,
        user_id=user.id,
        book_id=book.id,
    )

    assert result == "book_not_taken"


@pytest.mark.asyncio
async def test_return_book_service_returns_book_taken_by_other_user(db_session, clean_db):
    first_user = await create_user_or_get_existing(
        session=db_session,
        user_id=1007,
        full_name="reader_1",
        tg_username="reader_7",
        is_admin=False,
        contact="reader_7_contact"
    )

    second_user = await create_user_or_get_existing(
        session=db_session,
        user_id=1008,
        full_name="reader_2",
        tg_username="reader_8",
        is_admin=False,
        contact="reader_8_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Working Effectively with Legacy Code",
        description="Legacy code book",
    )

    take_result = await take_book_service(
        session=db_session,
        user_id=first_user.id,
        book_id=book.id,
    )
    assert take_result == "success"

    result = await return_book_service(
        session=db_session,
        user_id=second_user.id,
        book_id=book.id,
    )

    assert result == "book_taken_by_other_user"


@pytest.mark.asyncio
async def test_force_return_book_service_success(db_session, clean_db):
    admin = await create_user_or_get_existing(
        session=db_session,
        user_id=1009,
        full_name="admin_1",
        tg_username="admin_1",
        is_admin=True,
        contact="admin_1_contact"
    )

    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1010,
        full_name="reader_1",
        tg_username="reader_9",
        is_admin=False,
        contact="reader_9_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Code Complete",
        description="Engineering practices",
    )

    take_result = await take_book_service(
        session=db_session,
        user_id=user.id,
        book_id=book.id,
    )
    assert take_result == "success"

    result = await force_return_book_service(
        session=db_session,
        admin_id=admin.id,
        book_id=book.id,
    )

    assert result == "success"

    updated_book = await get_book_by_id_service(db_session, book.id)
    assert updated_book is not None
    assert updated_book.taken_by is None
    assert updated_book.taken_at is None


@pytest.mark.asyncio
async def test_force_return_book_service_returns_access_denied_for_non_admin(db_session, clean_db):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1011,
        full_name="reader_1",
        tg_username="not_admin",
        is_admin=False,
        contact="not_admin_contact"
    )

    owner = await create_user_or_get_existing(
        session=db_session,
        user_id=1012,
        full_name="reader_1",
        tg_username="reader_10",
        is_admin=False,
        contact="reader_10_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Soft Skills",
        description="Career book",
    )

    take_result = await take_book_service(
        session=db_session,
        user_id=owner.id,
        book_id=book.id,
    )
    assert take_result == "success"

    result = await force_return_book_service(
        session=db_session,
        admin_id=user.id,
        book_id=book.id,
    )

    assert result == "access_denied"


@pytest.mark.asyncio
async def test_force_return_book_service_returns_book_already_available(db_session, clean_db):
    admin = await create_user_or_get_existing(
        session=db_session,
        user_id=1013,
        full_name="reader_1",
        tg_username="admin_2",
        is_admin=True,
        contact="admin_2_contact"
    )

    book = await create_book_service(
        session=db_session,
        title="Introduction to Algorithms",
        description="CLRS",
    )

    result = await force_return_book_service(
        session=db_session,
        admin_id=admin.id,
        book_id=book.id,
    )

    assert result == "book_already_available"


@pytest.mark.asyncio
async def test_get_user_books_service_returns_taken_books(db_session, clean_db):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=1014,
        full_name="reader_1",
        tg_username="reader_11",
        is_admin=False,
        contact="reader_11_contact"
    )

    first_book = await create_book_service(
        session=db_session,
        title="Book One",
        description="First book",
    )

    second_book = await create_book_service(
        session=db_session,
        title="Book Two",
        description="Second book",
    )

    third_book = await create_book_service(
        session=db_session,
        title="Book Three",
        description="Third book",
    )

    assert await take_book_service(db_session, user.id, first_book.id) == "success"
    assert await take_book_service(db_session, user.id, second_book.id) == "success"

    books = await get_user_books_service(
        session=db_session,
        user_id=user.id,
    )

    returned_ids = {book.id for book in books}

    assert first_book.id in returned_ids
    assert second_book.id in returned_ids
    assert third_book.id not in returned_ids
    assert len(books) == 2
    
@pytest.mark.asyncio
async def test_take_book_service_returns_user_book_limit_reached_when_user_has_3_books(db_session):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=100001,
        full_name="Test User",
        tg_username="test_user",
        contact="+49111111111",
    )

    book_1 = await create_book_service(
        session=db_session,
        title="Book 1",
        description="Description 1",
    )
    book_2 = await create_book_service(
        session=db_session,
        title="Book 2",
        description="Description 2",
    )
    book_3 = await create_book_service(
        session=db_session,
        title="Book 3",
        description="Description 3",
    )
    book_4 = await create_book_service(
        session=db_session,
        title="Book 4",
        description="Description 4",
    )

    result_1 = await take_book_service(
        session=db_session,
        book_id=book_1.id,
        user_id=user.id,
    )
    result_2 = await take_book_service(
        session=db_session,
        book_id=book_2.id,
        user_id=user.id,
    )
    result_3 = await take_book_service(
        session=db_session,
        book_id=book_3.id,
        user_id=user.id,
    )

    result_4 = await take_book_service(
        session=db_session,
        book_id=book_4.id,
        user_id=user.id,
    )

    assert result_1 == "success"
    assert result_2 == "success"
    assert result_3 == "success"
    assert result_4 == "user_book_limit_reached"
    
@pytest.mark.asyncio
async def test_take_book_service_allows_new_book_after_return(db_session):
    user = await create_user_or_get_existing(
        session=db_session,
        user_id=100003,
        full_name="Return User",
        tg_username="return_user",
        contact="+49333333333",
    )

    book_1 = await create_book_service(session=db_session, title="Book 1", description="Desc 1")
    book_2 = await create_book_service(session=db_session, title="Book 2", description="Desc 2")
    book_3 = await create_book_service(session=db_session, title="Book 3", description="Desc 3")
    book_4 = await create_book_service(session=db_session, title="Book 4", description="Desc 4")

    assert await take_book_service(session=db_session, book_id=book_1.id, user_id=user.id) == "success"
    assert await take_book_service(session=db_session, book_id=book_2.id, user_id=user.id) == "success"
    assert await take_book_service(session=db_session, book_id=book_3.id, user_id=user.id) == "success"

    assert await take_book_service(session=db_session, book_id=book_4.id, user_id=user.id) == "user_book_limit_reached"

    assert await return_book_service(session=db_session, book_id=book_1.id, user_id=user.id) == "success"

    assert await take_book_service(session=db_session, book_id=book_4.id, user_id=user.id) == "success"