from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from ..texts import TEXTS

button_change_my_details = KeyboardButton(text=TEXTS['change_my_details'])
button_my_status = KeyboardButton(text="📊 Мой статус участия")
button_edit_meetings = KeyboardButton(text="🗓️ Изменить частоту встреч")
button_stop_participation = KeyboardButton(text="⏸️ Приостановить участие")
# button_start_participation = KeyboardButton(text="▶️ Возобновить участие")
button_how_it_works = KeyboardButton(text="❓ Как работает Random Coffee?")

# Кнопки для неактивных пользователей
button_resume_participation = KeyboardButton(text="▶️ Возобновить участие")
button_how_it_works_inactive = KeyboardButton(text="❓ Как работает Random Coffee?")


# Функция для создания клавиатуры для активных пользователей
def create_active_user_keyboard():
    buttons_kb_builder_user = ReplyKeyboardBuilder()
    buttons_kb_builder_user.row(
        button_change_my_details,
        button_my_status,
        button_edit_meetings,
        # button_start_participation,
        button_stop_participation,
        button_how_it_works,
        width=1
    )
    return buttons_kb_builder_user.as_markup(resize_keyboard=True)


# Функция для создания клавиатуры для неактивных пользователей
def create_inactive_user_keyboard():
    buttons_kb_builder_user = ReplyKeyboardBuilder()
    buttons_kb_builder_user.row(
        button_resume_participation,
        button_how_it_works_inactive,
        width=1
    )
    return buttons_kb_builder_user.as_markup(resize_keyboard=True)
