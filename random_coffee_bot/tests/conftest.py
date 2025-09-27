from collections.abc import AsyncIterator
from datetime import date, datetime, UTC

import pytest
import pytest_asyncio
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from random_coffee_bot.database.models import Base, Setting


@pytest.fixture(scope="session")
def pg_container():
    """Поднимаем Postgres в Docker на время всей сессии тестов."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


def make_async_url(pg_container) -> URL:
    return URL.create(
        drivername="postgresql+asyncpg",
        username=pg_container.username,
        password=pg_container.password,
        host=pg_container.get_container_host_ip(),
        port=pg_container.get_exposed_port(pg_container.port),
        database=pg_container.dbname,
    )


@pytest_asyncio.fixture
async def engine(pg_container) -> AsyncIterator[AsyncEngine]:
    """Создаём engine в том же loop, где будет идти тест."""

    async_url = make_async_url(pg_container)
    engine = create_async_engine(async_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine: AsyncEngine
                        ) -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий."""
    return async_sessionmaker(engine, expire_on_commit=False,
                              class_=AsyncSession)


@pytest_asyncio.fixture
async def session(session_maker: async_sessionmaker[AsyncSession]
                  ) -> AsyncIterator[AsyncSession]:
    """Одна сессия на тест с откатом в конце."""
    async with session_maker() as s:
        try:
            yield s
        finally:
            await s.rollback()


@pytest_asyncio.fixture
async def ensure_setting(session: AsyncSession):
    """Создаём запись Setting(id=1) с базовыми настройками."""
    setting = Setting(
        id=1,
        global_interval=2,
        first_pairing_date=datetime.now(UTC),
        is_pairing_on=True,
    )
    session.add(setting)
    await session.flush()
    return setting


@pytest.fixture
def utc_today() -> date:
    return datetime.now(UTC).date()
