import logging

from aiogram import Bot
from aiogram.types import (BotCommandScopeDefault,
                           BotCommandScopeChat,
                           MenuButtonCommands,
                           MenuButtonDefault)

from ..config import load_config
from ..main_menu import commands as c
from ..services.admin_service import get_admin_list


logger = logging.getLogger(__name__)


commands_for_super_admin = [
    c.command_admin_menu,
    c.command_user_menu,
    c.command_add_admin,
    c.command_remove_admin,
    c.command_admin_list]

commands_for_admin = [
    c.command_admin_menu,
    c.command_user_menu]


async def set_main_menu(bot: Bot, user_telegram_id: int, command_list: list):
    try:
        await bot.set_my_commands(commands=command_list,
                                  scope=BotCommandScopeChat(
                                      chat_id=user_telegram_id))
        await bot.set_chat_menu_button(chat_id=user_telegram_id,
                                       menu_button=MenuButtonCommands())
    except Exception:
        logger.info('Ошибка при отправке главного меню для '
                    f'админа {user_telegram_id}.')
        pass


async def delete_main_menu(bot: Bot, user_telegram_id: int):
    try:
        await bot.delete_my_commands(scope=BotCommandScopeChat(
                                     chat_id=user_telegram_id))
        await bot.set_chat_menu_button(chat_id=user_telegram_id,
                                       menu_button=MenuButtonDefault())
    except Exception:
        logger.info('Ошибка при удалении главного меню для '
                    f'админа {user_telegram_id}.')
        pass


async def set_main_menu_for_super_admins(bot: Bot):
    config = load_config()
    super_admins_tg_id_list = config.tg_bot.admins_list

    for admin_tg_id in super_admins_tg_id_list:
        await set_main_menu(bot, admin_tg_id, commands_for_super_admin)


async def set_main_menu_for_admins(bot: Bot):
    admins_list = await get_admin_list()

    for admin in admins_list:
        await set_main_menu(bot, admin.telegram_id, commands_for_admin)


async def set_main_menu_on_bot_start(bot: Bot):
    await bot.set_my_commands(commands=[], scope=BotCommandScopeDefault())
    await set_main_menu_for_admins(bot)
    await set_main_menu_for_super_admins(bot)
