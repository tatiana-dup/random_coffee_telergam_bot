from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from ..config import load_config


config = load_config()
admins_list = config.tg_bot.admins_list


class SuperAdminFilter(BaseFilter):
    """
    Фильтр проверяет, что пользователь является супер-админом.
    """
    async def __call__(self, event: Union[CallbackQuery, Message]) -> bool:
        user_telegram = getattr(event, "from_user", None)
        user_id = user_telegram.id if user_telegram else None
        return user_id in admins_list if user_id else False
