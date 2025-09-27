import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

from ..database.db import AsyncSessionLocal
from ..database.models import Setting


logger = logging.getLogger(__name__)


async def ensure_app_settings(default_global_interval: int | None,
                              first_pairing_at: datetime | None,
                              is_pairing_on: bool | None) -> Setting:
    """Создаёт запись setting(id=1), если её нет.
    Если запись уже есть — ничего не меняет.
    """

    async with AsyncSessionLocal() as session:
        try:
            stmt = pg_insert(Setting).values(
                id=1,
                global_interval=default_global_interval or 2,
                first_pairing_date=first_pairing_at,
                is_pairing_on=(is_pairing_on if is_pairing_on is not None
                               else False),
            ).on_conflict_do_nothing(index_elements=['id'])

            await session.execute(stmt)
            await session.commit()

            res = await session.execute(select(Setting).where(Setting.id == 1))
            return res.scalar_one()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f'Ошибка при внесении в БД базовых настроек: {e}.')
            raise
