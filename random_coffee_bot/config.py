from dataclasses import dataclass
from environs import Env
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass
class DatabaseConfig:
    db_url: str


@dataclass
class TgBot:
    token: str
    group_tg_id: int
    admins_list: list
    admin_username: str


@dataclass
class GoogleSheetConfig:
    sheet_id: str


@dataclass
class TimeConfig:
    name: str
    zone: ZoneInfo


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    g_sheet: GoogleSheetConfig
    time: TimeConfig


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    default_path = Path(__file__).resolve().parent / '.env'
    env.read_env(path or default_path)

    tz_name = env('DEFAULT_TZ')
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ValueError(
            f'Неизвестная таймзона с именем {tz_name}'
            'Проверьте значение DEFAULT_TZ в .env.'
        ) from e

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            group_tg_id=env.int('TELEGRAM_ID_PROJECT_GROUP'),
            admins_list=env.list('ADMIN_ID_LIST', subcast=int),
            admin_username=('ADMIN_TG_USERNAME')
        ),
        db=DatabaseConfig(
            db_url=env('DATABASE_URL')
        ),
        g_sheet=GoogleSheetConfig(
            sheet_id=env('GOOGLE_SHEET_ID')
        ),
        time=TimeConfig(
            name=tz_name,
            zone=tz
        )
    )
