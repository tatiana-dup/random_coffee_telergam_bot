from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

button_change_my_details = KeyboardButton(text="✏️ Изменить мои данные")
button_my_status = KeyboardButton(text="📊 Мой статус участия")
button_edit_meetings = KeyboardButton(text="🗓️ Изменить частоту встреч")
button_stop_participation = KeyboardButton(text="⏸️ Приостановить участие")
button_start_participation = KeyboardButton(text="▶️ Возобновить участие")
button_how_it_works = KeyboardButton(text="❓ Как работает Random Coffee?")

buttons_kb_builder_user = ReplyKeyboardBuilder()

buttons_kb_builder_user.row(
    button_change_my_details,
    button_my_status,
    button_edit_meetings,
    button_start_participation,
    button_stop_participation,
    button_how_it_works,
    width=1
)

buttons_kb_user = buttons_kb_builder_user.as_markup(
    resize_keyboard=True,
    # one_time_keyboard=True,
)