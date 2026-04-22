from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.book_repository import (
    count_books,
    create_book,
    delete_book,
    force_return_book,
    get_all_books,
    get_book_by_id,
    get_books_by_user_id,
    get_books_page,
    get_taken_books,
    return_book_if_taken_by_user,
    take_book_if_available,
    update_book,
    count_available_books,
    count_taken_books,
)
from db.repositories.logger_repository import create_log_entry
from db.repositories.user_repository import get_user_by_id


async def create_book_service(
    session: AsyncSession,
    title: str,
    author: str | None,
    publisher: str | None,
    genre: str | None,
    language: str | None,
    description: str | None,
):
    book = await create_book(
        session=session,
        title=title,
        author=author,
        publisher=publisher,
        genre=genre,
        language=language,
        description=description,
    )

    await create_log_entry(
        session,
        "create_book",
        None,
        book.id,
        book.title,
        user_full_name=None,
    )
    return book


async def get_book_by_id_service(
    session: AsyncSession,
    book_id: int,
):
    return await get_book_by_id(session, book_id)


async def get_user_books_service(
    session: AsyncSession,
    user_id: int,
):
    return await get_books_by_user_id(session, user_id)


async def take_book_service(
    session: AsyncSession,
    user_id: int,
    book_id: int,
) -> str:
    user = await get_user_by_id(session, user_id)
    if user is None:
        return "user_not_found"

    user_books = await get_books_by_user_id(session, user_id)
    if len(user_books) >= 3:
        return "user_book_limit_reached"

    book = await get_book_by_id(session, book_id)
    if book is None:
        return "book_not_found"

    success = await take_book_if_available(session, book_id, user_id)
    if not success:
        return "book_already_taken"

    await create_log_entry(
        session,
        "take",
        user_id,
        book_id,
        book.title,
        user.full_name,
    )
    return "success"


async def return_book_service(
    session: AsyncSession,
    user_id: int,
    book_id: int,
) -> str:
    user = await get_user_by_id(session, user_id)
    if user is None:
        return "user_not_found"

    book = await get_book_by_id(session, book_id)
    if book is None:
        return "book_not_found"

    if book.taken_by is None:
        return "book_not_taken"

    success = await return_book_if_taken_by_user(session, book_id, user_id)
    if not success:
        return "book_taken_by_other_user"

    await create_log_entry(
        session,
        "return",
        user_id,
        book_id,
        book.title,
        user.full_name,
    )
    return "success"


async def force_return_book_service(
    session: AsyncSession,
    admin_id: int,
    book_id: int,
) -> str:
    admin = await get_user_by_id(session, admin_id)
    if admin is None:
        return "user_not_found"

    if not admin.is_admin:
        return "access_denied"

    book = await get_book_by_id(session, book_id)
    if book is None:
        return "book_not_found"

    if book.taken_by is None:
        return "book_already_available"

    success = await force_return_book(session, book_id)
    if not success:
        return "force_return_failed"

    await create_log_entry(
        session,
        "forced_return",
        admin_id,
        book_id,
        book.title,
        None,
    )
    return "success"


async def update_book_service(
    session: AsyncSession,
    book_id: int,
    title: str | None = None,
    author: str | None = None,
    publisher: str | None = None,
    genre: str | None = None,
    language: str | None = None,
    description: str | None = None,
):
    if all(
        value is None
        for value in (title, author, publisher, genre, language, description)
    ):
        return "nothing_to_update"

    book = await update_book(
        session=session,
        book_id=book_id,
        title=title,
        author=author,
        publisher=publisher,
        genre=genre,
        language=language,
        description=description,
    )

    if book is None:
        return "book_not_found"

    await create_log_entry(
        session,
        "update_book",
        None,
        book.id,
        book.title,
        user_full_name=None,
    )
    return book


async def delete_book_service(
    session: AsyncSession,
    book_id: int,
) -> str:
    book = await get_book_by_id(session, book_id)
    if book is None:
        return "book_not_found"

    if book.taken_by is not None:
        return "book_is_taken"

    deleted = await delete_book(
        session=session,
        book_id=book_id,
    )

    if not deleted:
        return "book_not_found"

    await create_log_entry(
        session,
        "delete_book",
        None,
        book_id,
        book.title,
        user_full_name=None,
    )
    return "success"


async def get_all_books_service(session: AsyncSession) -> list:
    return await get_all_books(session)


async def get_books_page_service(
    session: AsyncSession,
    limit: int,
    offset: int,
    filter_type: str | None = None,
):
    return await get_books_page(
        session=session,
        limit=limit,
        offset=offset,
        filter_type=filter_type,
    )


async def count_books_service(session: AsyncSession) -> int:
    return await count_books(session)


async def count_available_books_service(session):
    return await count_available_books(session)


async def count_taken_books_service(session):
    return await count_taken_books(session)

async def get_taken_books_service(session: AsyncSession):
    return await get_taken_books(session)