from typing import Optional, Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from ..database.db import AsyncSessionLocal
from ..database.models import User
from ..services.user_service import get_user_from_event


class ActiveUserFilter(BaseFilter):
    """
    Фильтр проверяет, что юзер есть в БД и имеет статус "активен".
    """
    async def __call__(self, event: Union[CallbackQuery, Message]) -> bool:
        async with AsyncSessionLocal() as session:
            user: Optional[User] = await get_user_from_event(session, event)
        return user.is_active if user else False


class InactiveUserFilter(BaseFilter):
    """
    Фильтр проверяет, что юзер есть в БД и имеет статус "неактивен".
    """
    async def __call__(self, event: Union[CallbackQuery, Message]) -> bool:
        async with AsyncSessionLocal() as session:
            user: Optional[User] = await get_user_from_event(session, event)
        return not user.is_active if user else False
