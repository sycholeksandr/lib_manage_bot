import os

import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.user import User
from db.models.book import Book
from db.models.logger import Logger
from core.config import settings

import sys
import asyncio


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



TEST_DATABASE_URL = settings.TEST_DATABASE_URL
if not TEST_DATABASE_URL:
    raise ValueError("TEST_DATABASE_URL is not set")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,

    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def clean_db(session_factory):
    async with session_factory() as session:
        await session.execute(delete(Logger))
        await session.execute(delete(Book))
        await session.execute(delete(User))
        await session.commit()

    yield

    async with session_factory() as session:
        await session.execute(delete(Logger))
        await session.execute(delete(Book))
        await session.execute(delete(User))
        await session.commit()