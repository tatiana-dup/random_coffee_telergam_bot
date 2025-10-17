import logging

from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.exc import SQLAlchemyError

from ..database.db import AsyncSessionLocal
from ..keyboards.user_buttons import create_active_user_keyboard
from ..services.user_service import (create_user,
                                     get_user_by_telegram_id,
                                     set_user_active,
                                     update_username)
from ..states.user_states import FSMUserForm
from ..texts import USER_TEXTS


logger = logging.getLogger(__name__)


user_start_router = Router()


@user_start_router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message, state: FSMContext):
    """
    Хэндлер для команды /start. Регистрирует нового пользователя.
    Если поль-ль уже существует, обновляет его статус is_active = True.
    """
    logger.debug('Вошли в хэндлер, обрабатывающий команду /start')
    if message.from_user is None:
        return await message.answer(USER_TEXTS['error_access'])

    user_telegram_id = message.from_user.id

    try:
        async with AsyncSessionLocal() as session:
            user = await get_user_by_telegram_id(session, user_telegram_id)

            if user is None:
                logger.debug('Пользователя нет в БД. Приступаем к добавлению.')
                user = await create_user(session,
                                         user_telegram_id,
                                         message.from_user.username,
                                         message.from_user.first_name,
                                         message.from_user.last_name)
                logger.debug(f'Пользователь добавлен в БД. '
                             f'Имя {user.first_name}. Фамилия {user.last_name}'
                             )
                await message.answer(USER_TEXTS['start'])
                await message.answer(USER_TEXTS['ask_first_name'])
                await state.set_state(FSMUserForm.waiting_for_first_name)
            else:
                if not user.is_active:
                    await set_user_active(session, user_telegram_id, True)
                    logger.debug('Статус пользователя изменен на Активный.')
                await update_username(session, user_telegram_id,
                                      message.from_user.username)
                await message.answer(
                    USER_TEXTS['re_start'],
                    reply_markup=create_active_user_keyboard())
    except SQLAlchemyError as e:
        logger.error('Ошибка при работе с базой данных: %s', str(e))
        await message.answer(USER_TEXTS['db_error'])
