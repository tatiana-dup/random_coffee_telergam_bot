from aiogram.types import BotCommand

from ..texts import COMMANDS_DESCRIPTION_TEXT


command_add_admin = BotCommand(command='/add_admin',
                               description=COMMANDS_DESCRIPTION_TEXT['add_admin'])

command_remove_admin = BotCommand(command='/remove_admin',
                                  description=COMMANDS_DESCRIPTION_TEXT['remove_admin'])

command_admin_list = BotCommand(command='/admin_list',
                                description=COMMANDS_DESCRIPTION_TEXT['admin_list'])

command_user_menu = BotCommand(command='/user_menu',
                               description=COMMANDS_DESCRIPTION_TEXT['user_menu'])

command_admin_menu = BotCommand(command='/admin_menu',
                                description=COMMANDS_DESCRIPTION_TEXT['admin_menu'])
