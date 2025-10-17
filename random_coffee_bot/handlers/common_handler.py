import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.exceptions import (AiogramError,
                                TelegramAPIError,
                                TelegramBadRequest,
                                TelegramForbiddenError,
                                TelegramNetworkError,
                                TelegramRetryAfter)
from aiogram.types import CallbackQuery, ErrorEvent, Message

from ..database.db import AsyncSessionLocal
from ..services.user_service import create_text_random_coffee
from ..texts import KEYBOARD_BUTTON_TEXTS, USER_TEXTS


logger = logging.getLogger(__name__)

common_router = Router()


@common_router.message(
        F.text == KEYBOARD_BUTTON_TEXTS['button_how_it_works'],
        StateFilter(default_state))
async def text_random_coffee(message: Message):
    """
    Выводит текст о том как работает Random_coffee
    """
    async with AsyncSessionLocal() as session:
        text = await create_text_random_coffee(session)
        await message.answer(text, parse_mode='HTML')


@common_router.message(Command('help'), StateFilter(default_state))
async def proccess_comand_help(message: Message):
    """
    Хэндлер обрабатывает команду /help.
    """
    await message.answer(USER_TEXTS['command_help'], parse_mode='HTML')


@common_router.message(F.text, StateFilter(default_state))
async def fallback_handler(message: Message):
    """
    Хэндлер срабатывает, когда юзер отправляет неизвестную
    команду или просто текст, который мы не ожидаем.
    """
    await message.answer(USER_TEXTS['no_now'])


@common_router.message(StateFilter(default_state))
async def other_type_handler(message: Message):
    """
    Хэндлер срабатывает, когда юзер отправляет что-то кроме текста,
    что бот не может обработать.
    """
    await message.answer(USER_TEXTS['user_unknown_type_data'])


@common_router.callback_query()
async def missed_callback(callback: CallbackQuery):
    """
    Хэндлер будет обрабатывать коллбеки, которые устарели или потеряли
    данные из-за перезапуска бота.
    """
    try:
        if isinstance(callback.message, Message):
            await callback.message.delete()
    except Exception:
        pass
    await callback.answer(USER_TEXTS['old_callback'], show_alert=True)


@common_router.error()
async def global_error_handler(event: ErrorEvent) -> bool:
    """
    Глобальный хэндлер ошибок. Возвращает True, чтобы aiogram не прокидывал
    исключение дальше, и бот не падал.
    """
    chat_id = None
    if event.update.message:
        chat_id = event.update.message.chat.id
    elif event.update.callback_query and event.update.callback_query.message:
        chat_id = event.update.callback_query.message.chat.id

    if isinstance(event.exception, TelegramRetryAfter):
        logger.warning('Превышен лимит запросов')

    elif isinstance(event.exception, TelegramForbiddenError):
        logger.error(f'Сообщение не доставлено. '
                     f'Юзер {chat_id or "неизвестный"} заблокировал бота.')

    elif isinstance(event.exception, TelegramBadRequest):
        text = str(event.exception).lower()
        if ('message is not modified' in text
                or 'message to edit not found' in text):
            return True
        logger.error('BadRequest при работе с '
                     f'Telegram API: {event.exception}')

    elif isinstance(event.exception, TelegramNetworkError):
        logger.warning(f'Проблемы с интернет-соединением при запросе '
                       f'к Telegram API: {event.exception}')

    elif isinstance(event.exception, TelegramAPIError):
        logger.exception(f'TelegramAPIError: {event.exception}')

    elif isinstance(event.exception, AiogramError):
        logger.exception(f'Aiogram ошибка: {event.exception}')

    else:
        logger.exception(f'Необработанное исключение: {event.exception}')

    return True
