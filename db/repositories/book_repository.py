from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.book import Book
from datetime import datetime, UTC


async def get_book_by_id(session: AsyncSession, book_id: int) -> Book | None:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_book(
    session: AsyncSession,
    title: str,
    description: str
) -> Book:
    new_book = Book(
        title=title,
        description=description
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

async def take_book_if_available(session: AsyncSession, book_id: int, taken_by: int) -> bool:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None or book.taken_by is not None:
        return False

    book.taken_by = taken_by
    book.taken_at = datetime.now(UTC)
    await session.commit()
    return True

async def return_book_if_taken_by_user(session: AsyncSession, book_id: int, taken_by: int) -> bool:
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
    description: str | None = None,
) -> Book | None:
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if book is None:
        return None

    if title is not None:
        book.title = title

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
    stmt = select(Book)
    result = await session.execute(stmt)
    return result.scalars().all()