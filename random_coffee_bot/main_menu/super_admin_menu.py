import logging

from aiogram import Bot
from aiogram.types import (BotCommand,
                           BotCommandScopeDefault,
                           BotCommandScopeChat,
                           MenuButtonCommands)

from config import load_config
from services.admin_service import get_admin_list


logger = logging.getLogger(__name__)

config = load_config()
super_admins_list = config.tg_bot.admins_list


async def set_super_admin_main_menu(bot: Bot):

    super_admin_commands = [
        BotCommand(command='/add_admin',
                   description='Дать роль админа'),
        BotCommand(command='/remove_admin',
                   description='Забрать роль админа'),
        BotCommand(command='/admin_list',
                   description='Список админов'),
        BotCommand(command='/user_menu',
                   description='Меню обычного пользователя'),
        BotCommand(command='/admin_menu',
                   description='Меню админа'),
    ]

    admins_list = await get_admin_list()

    admin_commands = [
        BotCommand(command='/user_menu',
                   description='Меню обычного пользователя'),
        BotCommand(command='/admin_menu',
                   description='Меню админа'),
    ]

    await bot.set_my_commands(commands=[], scope=BotCommandScopeDefault())

    for admin in admins_list:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=admin.telegram_id))

            await bot.set_chat_menu_button(
                chat_id=admin.telegram_id,
                menu_button=MenuButtonCommands()
            )
        except Exception:
            logger.debug('Ошибка при отображении главного меню для '
                         f'админа {admin.telegram_id}.')
            pass

    for admin_id in super_admins_list:
        try:
            await bot.set_my_commands(
                commands=super_admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id))

            await bot.set_chat_menu_button(
                chat_id=admin_id,
                menu_button=MenuButtonCommands()
            )
        except Exception:
            logger.debug('Ошибка при отображении главного меню для СУПЕР '
                         f'админа {admin_id}.')
            pass
