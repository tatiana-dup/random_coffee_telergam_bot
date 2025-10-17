import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from ..database.db import AsyncSessionLocal
from ..filters.user_filter import InactiveUserFilter
from ..keyboards.user_buttons import (create_active_user_keyboard,
                                      create_activate_keyboard,
                                      create_inactive_user_keyboard)
from ..services.user_service import (create_text_random_coffee,
                                     get_user_by_telegram_id,
                                     set_user_active,
                                     update_username)
from ..texts import KEYBOARD_BUTTON_TEXTS, USER_TEXTS


logger = logging.getLogger(__name__)

inactive_user_router = Router()
inactive_user_router.message.filter(InactiveUserFilter())
inactive_user_router.callback_query.filter(InactiveUserFilter())


@inactive_user_router.message(
    F.text == KEYBOARD_BUTTON_TEXTS['button_resume_participation'],
    StateFilter(default_state)
)
async def resume_participation(message: Message):
    """
    Хэндлер для возобновления участия пользователя.
    """
    telegram_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

    if user and not user.is_active:
        await message.answer(
            USER_TEXTS['confirm_resume'],
            reply_markup=create_activate_keyboard()
        )
    else:
        await message.answer(USER_TEXTS['status_active'])


@inactive_user_router.callback_query(
        lambda c: c.data.startswith('confirm_activate_'),
        StateFilter(default_state))
async def process_activate_confirmation(callback_query: CallbackQuery):
    """
    Хэндлер для обработки подтверждения возобновления участия.
    """
    telegram_id = callback_query.from_user.id

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        if user is None:
            await callback_query.answer(
                USER_TEXTS['user_not_found'],
                show_alert=True
            )
            return

        try:
            await callback_query.message.delete()

            if callback_query.data == 'confirm_activate_yes':
                if not user.is_active:
                    await set_user_active(session, telegram_id, True)
                    await update_username(session, telegram_id,
                                          callback_query.from_user.username)
                    await callback_query.message.answer(
                        USER_TEXTS['participation_resumed'],
                        reply_markup=create_active_user_keyboard()
                    )
                else:
                    await callback_query.answer(
                        USER_TEXTS['status_active'],
                        show_alert=True
                    )

            elif callback_query.data == 'confirm_activate_no':
                await callback_query.answer(
                    USER_TEXTS['status_not_changed'],
                    show_alert=True
                )

            await callback_query.answer()

        except Exception as e:
            logger.error(f'Произошла ошибка: {e}')
            await callback_query.answer(
                USER_TEXTS['error_occurred'],
                show_alert=True
            )


@inactive_user_router.message(
        F.text == KEYBOARD_BUTTON_TEXTS['button_how_it_works'],
        StateFilter(default_state))
async def text_random_coffee(message: Message):
    """
    Выводит текст о том как работает Random_coffee
    """
    async with AsyncSessionLocal() as session:
        text = await create_text_random_coffee(session)
        await message.answer(text, parse_mode='HTML')


@inactive_user_router.message(F.text.in_(KEYBOARD_BUTTON_TEXTS.values()),
                              StateFilter(default_state))
async def process_change_kb_from_active_to_inactive(message: Message):
    """
    Хэндлер будет отправлять юзеру клавиатуру для неактивного статуса в
    ответ на тексты с кнопок, которые не должны быть доступны для
    неактивного юзера.
    """
    await message.answer(USER_TEXTS['ask_to_use_active_kb'],
                         reply_markup=create_inactive_user_keyboard())
