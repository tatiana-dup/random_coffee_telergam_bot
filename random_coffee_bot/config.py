from dataclasses import dataclass
from datetime import datetime
from environs import Env
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .utils.timeparse import parse_iso_to_utc, TimeParseError


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
class BootstrapSettings:
    first_pairing_at: datetime


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig
    g_sheet: GoogleSheetConfig
    time: TimeConfig
    bs_settings: BootstrapSettings


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

    raw = env('FIRST_PAIRING_AT')
    try:
        first_pairing_at = parse_iso_to_utc(raw)
    except TimeParseError as e:
        raise ValueError(
            'Дата первого формирования пар не задана или задана неверно.'
        ) from e

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            group_tg_id=env.int('TELEGRAM_ID_PROJECT_GROUP'),
            admins_list=[int(x) for x in env.str('ADMIN_ID_LIST', ''
                                                 ).split(',') if x.strip()],
            admin_username=env('ADMIN_TG_USERNAME')
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
        ),
        bs_settings=BootstrapSettings(
            first_pairing_at=first_pairing_at
        )
    )
