import logging
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext

from ..filters.super_admin_filters import (
    SuperAdminMessageFilter,
    SuperAdminCallbackFilter
)
from ..main_menu.main_menu_setup import (commands_for_admin,
                                       delete_main_menu,
                                       set_main_menu)
from ..states.admin_states import FSMAdminPanel
from ..services.admin_service import (
    set_user_as_admin,
    set_admin_as_user,
    is_user_admin,
    is_admin_user,
    get_admin_list
)
from ..keyboards.admin_buttons import buttons_kb_admin
from ..keyboards.user_buttons import (create_active_user_keyboard,
                                    create_inactive_user_keyboard)
from ..texts import ADMIN_TEXTS, KEYBOARD_BUTTON_TEXTS

logger = logging.getLogger(__name__)

super_admin_router = Router()

super_admin_router.message.filter(SuperAdminMessageFilter())
super_admin_router.callback_query.filter(SuperAdminCallbackFilter())


@super_admin_router.message(Command('add_admin'), StateFilter(default_state))
async def cmd_add_admin(message: Message, state: FSMContext):
    """Хэндлер для команды добаления админа командой /add_admin."""
    await message.answer(ADMIN_TEXTS['prompt_for_user_id'])
    await state.set_state(FSMAdminPanel.waiting_for_user_id)


@super_admin_router.message(
    Command('cancel'),
    StateFilter(FSMAdminPanel.waiting_for_user_id)
)
async def cancel_admin_handler(message: Message, state: FSMContext):
    """Хэндлер для остановки добавления админа командой /cancel."""
    await state.clear()
    await message.answer(ADMIN_TEXTS['creation_cancelled'])


@super_admin_router.message(StateFilter(FSMAdminPanel.waiting_for_user_id))
async def process_user_id(message: Message, state: FSMContext):
    """Хэндлер для ввода ID пользователя, которого хотим сделать админом."""
    if message.text in KEYBOARD_BUTTON_TEXTS.values():
        await message.answer(ADMIN_TEXTS['no_kb_buttons'])
        await message.answer(ADMIN_TEXTS['prompt_for_user_id'])
        return

    user_id_str = message.text

    if isinstance(user_id_str, str) and user_id_str.isdigit():
        user_id = int(user_id_str)

        if await is_user_admin(user_id):
            await message.answer(ADMIN_TEXTS['user_already_admin'])
            await state.clear()
            return

        success = await set_user_as_admin(user_id)

        if success:
            await message.answer(
                ADMIN_TEXTS['user_is_admin_now'].format(user_id=user_id))

            key = StorageKey(
                user_id=user_id,
                chat_id=user_id,
                bot_id=message.bot.id
            )
            user_ctx = FSMContext(storage=state.storage, key=key)
            await user_ctx.clear()

            await set_main_menu(message.bot, user_id, commands_for_admin)
            await message.bot.send_message(
                user_id,
                ADMIN_TEXTS['now_admin_message'],
                reply_markup=buttons_kb_admin
            )

            await state.clear()
        else:
            await message.answer(
                ADMIN_TEXTS['user_for_admin_is_not_find'
                            ].format(user_id=user_id))
    else:
        logger.debug('Было введено не ID пользователя.')
        await message.answer(ADMIN_TEXTS['invalid_user_id_input'])


@super_admin_router.message(
    Command('remove_admin'),
    StateFilter(default_state)
)
async def cmd_remove_admin(message: Message, state: FSMAdminPanel):
    """Хэндлер для удаления не главного админа командой /remove_admin."""
    await message.answer(ADMIN_TEXTS['prompt_for_admin_id'])
    await state.set_state(FSMAdminPanel.waiting_for_admin_id)


@super_admin_router.message(
    Command('cancel'),
    StateFilter(FSMAdminPanel.waiting_for_admin_id)
)
async def cancel_user_handler(message: Message, state: FSMContext):
    """Остановка удаления не главного админа командой /cancel."""
    await state.clear()
    await message.answer(ADMIN_TEXTS['deletion_cancelled'])


@super_admin_router.message(StateFilter(FSMAdminPanel.waiting_for_admin_id))
async def process_admin_id(message: Message, state: FSMContext):
    """Ввод ID не главного админа которого хочешь удалить."""
    if message.text in KEYBOARD_BUTTON_TEXTS.values():
        await message.answer(ADMIN_TEXTS['no_kb_buttons'])
        await message.answer(ADMIN_TEXTS['prompt_for_admin_id'])
        return

    user_id_str = message.text
    if isinstance(user_id_str, str) and user_id_str.isdigit():
        user_id = int(user_id_str)

        if await is_admin_user(user_id):
            await message.answer(
                ADMIN_TEXTS['invalid_admin_user']
            )
            await state.clear()
            return

        success, user = await set_admin_as_user(user_id)

        if success:
            keyboard = (create_active_user_keyboard() if user.is_active
                        else create_inactive_user_keyboard())
            await message.answer(
                ADMIN_TEXTS['admin_is_user_now'].format(user_id=user_id))

            key = StorageKey(
                user_id=user_id,
                chat_id=user_id,
                bot_id=message.bot.id
            )
            user_ctx = FSMContext(storage=state.storage, key=key)
            await user_ctx.clear()

            await delete_main_menu(message.bot, user_id)
            await message.bot.send_message(
                user_id,
                ADMIN_TEXTS['no_admin_anymore'],
                reply_markup=keyboard)
            await state.clear()

        else:
            await message.answer(
                ADMIN_TEXTS['admin_for_user_is_not_found'
                            ].format(user_id=user_id))

    else:
        logger.debug('Было введено не ID администратора.')
        await message.answer(
            ADMIN_TEXTS['invalid_admin_id']
        )


@super_admin_router.message(Command('admin_list'), StateFilter(default_state))
async def admin_list_handler(message: Message):
    """Хэндлер для команды /admin_list, выводит список всех администраторов."""
    admins = await get_admin_list()

    if not admins:
        await message.answer(ADMIN_TEXTS['empty_admin_list'])
        return

    admin_ids = [
        f'ID: {admin.telegram_id} - {admin.first_name} {admin.last_name or " "}'
        for admin in admins
    ]
    admin_list_message = '\n'.join(admin_ids)

    await message.answer(
        ADMIN_TEXTS['admin_list'].format(
            admin_list_message=admin_list_message))


# Служебный хэндлер на время разработки
@super_admin_router.message(Command('del'), StateFilter(default_state))
async def remove_me_from_db(message: Message):
    from services.admin_service import delete_user
    await delete_user(message.from_user.id)
    await message.answer('Готово')
