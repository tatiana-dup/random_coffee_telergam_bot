import logging
from datetime import datetime, timezone
from typing import Optional

from aiogram import Bot
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from ..config import load_config
from ..database.db import AsyncSessionLocal
from ..database.models import Setting
from ..services.constants import DATE_TIME_FORMAT_LOCALTIME
from ..texts import ADMIN_TEXTS


logger = logging.getLogger(__name__)

config = load_config()
bot_timezone = config.time.zone
db_url = config.db.db_url

DATABASE_URL = db_url.replace('+asyncpg', '+psycopg')

scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=DATABASE_URL)
    },
    timezone='UTC'
)

PAIRING_JOB_ID = 'testing'

_BOT: Optional[Bot] = None


def set_bot(bot: Bot) -> None:
    global _BOT
    _BOT = bot


def get_bot() -> Bot:
    assert _BOT is not None, "Bot is not initialized yet"
    return _BOT


async def get_settings() -> Setting:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Setting).where(Setting.id == 1))
        return result.scalar_one()


async def start_scheduler(bot: Bot):
    set_bot(bot)

    if not scheduler.running:
        scheduler.start()

    job = scheduler.get_job(PAIRING_JOB_ID)
    if not job:
        settings = await get_settings()

        add_pairing_job(scheduler,
                        job_id=PAIRING_JOB_ID,
                        first_date=datetime(2025, 10, 9, 11, 50,
                                            tzinfo=timezone.utc),
                        interval=settings.global_interval)


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def add_pairing_job(scheduler: AsyncIOScheduler,
                    job_id: str,
                    first_date: datetime,
                    interval: int):
    scheduler.add_job(send_to_me,
                      trigger=IntervalTrigger(minutes=interval,
                                              start_date=first_date),
                      id=job_id,
                      misfire_grace_time=60,
                      replace_existing=True)


def change_interval(new_interval):
    scheduler.modify_job(job_id=PAIRING_JOB_ID,
                         trigger=IntervalTrigger(minutes=new_interval))


def pause_pairing():
    scheduler.pause()


def resume_pairing():
    scheduler.resume()


async def send_to_me():
    bot = get_bot()
    next_run_text = get_next_pairing_date()
    await bot.send_message(
        chat_id=269444415,
        text=f'Задача выполнена. Следующий запуск {next_run_text}')


def get_next_pairing_date() -> str | None:
    """
    Возвращает дату, когда состоится следующее формирование пар
    согласно планировщику задач.
    """
    job = scheduler.get_job(PAIRING_JOB_ID)

    if job:
        next_run_utc = job.next_run_time

        if not next_run_utc:
            logger.info(f'🛠 Паринг остановлен. Но задача {job.id} '
                        f'запланирована на: {next_run_utc}')
            return ADMIN_TEXTS['pairing_on_pause'
                               ].format(next_run_str='None')
        else:
            next_run_localtime = next_run_utc.astimezone(bot_timezone)
            next_run_str = next_run_localtime.strftime(DATE_TIME_FORMAT_LOCALTIME)
            logger.debug(f'🛠 Задача {job.id} запустится: {next_run_str}')
            return next_run_str
    return None
