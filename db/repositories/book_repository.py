from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.book import Book


async def get_book_by_id(session: AsyncSession, book_id: int) -> Book | None:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_book(
    session: AsyncSession,
    title: str,
    author: str | None,
    publisher: str | None,
    genre: str | None,
    language: str | None,
    description: str | None,
) -> Book:
    new_book = Book(
        title=title,
        author=author,
        publisher=publisher,
        genre=genre,
        language=language,
        description=description,
    )

    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)

    return new_book


async def get_books_by_user_id(session: AsyncSession, taken_by: int) -> list[Book]:
    stmt = select(Book).where(Book.taken_by == taken_by)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_taken_books(session: AsyncSession) -> list[Book]:
    stmt = select(Book).where(Book.taken_by.is_not(None))
    result = await session.execute(stmt)
    return result.scalars().all()


async def take_book_if_available(
    session: AsyncSession,
    book_id: int,
    taken_by: int,
) -> bool:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None or book.taken_by is not None:
        return False

    book.taken_by = taken_by
    book.taken_at = datetime.now(UTC)
    await session.commit()
    return True


async def return_book_if_taken_by_user(
    session: AsyncSession,
    book_id: int,
    taken_by: int,
) -> bool:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None or book.taken_by != taken_by:
        return False

    book.taken_by = None
    book.taken_at = None
    await session.commit()
    return True


async def force_return_book(session: AsyncSession, book_id: int) -> bool:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None:
        return False

    book.taken_by = None
    book.taken_at = None
    await session.commit()
    return True


async def update_book(
    session: AsyncSession,
    book_id: int,
    title: str | None = None,
    author: str | None = None,
    publisher: str | None = None,
    genre: str | None = None,
    language: str | None = None,
    description: str | None = None,
) -> Book | None:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None:
        return None

    if title is not None:
        book.title = title

    if author is not None:
        book.author = author

    if publisher is not None:
        book.publisher = publisher

    if genre is not None:
        book.genre = genre

    if language is not None:
        book.language = language

    if description is not None:
        book.description = description

    await session.commit()
    await session.refresh(book)

    return book


async def delete_book(
    session: AsyncSession,
    book_id: int,
) -> bool:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None:
        return False

    await session.delete(book)
    await session.commit()

    return True


async def get_all_books(session: AsyncSession) -> list[Book]:
    stmt = select(Book).order_by(Book.id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_books_page(
    session: AsyncSession,
    limit: int,
    offset: int,
) -> list[Book]:
    stmt = select(Book).order_by(Book.id).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()


async def count_books(session: AsyncSession) -> int:
    stmt = select(func.count(Book.id))
    result = await session.execute(stmt)
    return result.scalar_one()