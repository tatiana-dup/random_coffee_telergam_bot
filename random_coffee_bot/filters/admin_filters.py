from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from ..database.db import AsyncSessionLocal
from ..config import load_config
from ..services.user_service import get_user_by_telegram_id


config = load_config()
admins_list = config.tg_bot.admins_list


class AdminFilter(BaseFilter):
    """
    Фильтр проверяет, что пользователь является админом (обычным или супер)
    """
    async def __call__(self, event: Union[CallbackQuery, Message]) -> bool:
        user_telegram = getattr(event, "from_user", None)
        user_tg_id = user_telegram.id if user_telegram else None

        if not user_tg_id:
            return False

        if user_tg_id in admins_list:
            return True

        async with AsyncSessionLocal() as session:
            user = await get_user_by_telegram_id(session, user_tg_id)
            return user.is_admin if user else False
