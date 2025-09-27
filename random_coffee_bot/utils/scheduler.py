import logging
from datetime import datetime, timedelta, timezone

from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from ..config import load_config
from ..database.db import AsyncSessionLocal
from ..database.models import Setting
from ..globals import job_context
from ..services.constants import DATE_TIME_FORMAT_LOCALTIME
from ..texts import ADMIN_TEXTS
from ..utils.pairing import auto_pairing


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

current_interval = None


async def auto_pairing_wrapper():
    bot, dispatcher, session_maker = job_context.get_context()

    async with session_maker() as session:
        result = await session.execute(select(Setting.is_pairing_on)
                                       .where(Setting.id == 1))
        is_pairing_on = result.scalar_one()

        if not is_pairing_on:
            logger.info('🛑 Задача auto_pairing_weekly приостановлена '
                        '(флаг в настройках).')
            return

    await auto_pairing(session_maker, bot)


async def reload_scheduled_wrapper():
    _, _, session_maker = job_context.get_context()
    await reload_scheduled_jobs(session_maker)


# отображение для консоли
def show_next_runs(scheduler: AsyncIOScheduler):
    logger.debug('🔔 Расписание ближайших запусков задач:')

    for job in scheduler.get_jobs():
        next_run_utc = job.next_run_time
        next_run_localtime = next_run_utc.astimezone(bot_timezone)
        logger.debug(f'🛠 Задача "{job.id}" запустится в: '
                     f'{next_run_localtime.strftime(DATE_TIME_FORMAT_LOCALTIME) if next_run_localtime else "нет запланированного запуска"}')


async def get_next_pairing_date() -> str | None:
    """
    Возвращает дату, когда состоится следующее формирование пар
    согласно планировщику задач.
    """
    job = next((job for job in scheduler.get_jobs()
                if job.id == 'auto_pairing_weekly'), None)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Setting.is_pairing_on)
                                       .where(Setting.id == 1))
        is_pairing_on = result.scalar_one()

    if job:
        next_run_utc = job.next_run_time
        next_run_localtime = next_run_utc.astimezone(bot_timezone)
        next_run_str = next_run_localtime.strftime(DATE_TIME_FORMAT_LOCALTIME)

        if not is_pairing_on:
            logger.info(f'🛠 Паринг остановлен. Но задача {job.id} '
                        f'запланирована на: {next_run_str}')
            return ADMIN_TEXTS['pairing_on_pause'
                               ].format(next_run_str=next_run_str)
        else:
            logger.debug(f'🛠 Задача {job.id} запустится: {next_run_str}')
            return next_run_str
    return None


# отображение для консоли
def job_listener(event):
    show_next_runs(scheduler)


async def schedule_feedback_dispatcher_for_auto_pairing(
        start_date_for_auto_pairing):
    start_date_for_feedback_dispatcher = start_date_for_auto_pairing - timedelta(minutes=3)  # Для прода должно стоять days
    return start_date_for_feedback_dispatcher


def schedule_or_reschedule(job_id, func, recieved_interval, session_maker,
                           start_date=None,
                           misfire_grace_time: int | None = None):
    job = scheduler.get_job(job_id)
    now = datetime.now(timezone.utc)
    effective_start = start_date or now

    if job:
        current_job_interval = job.trigger.interval.total_seconds() // 60  # Для тестирования в часах 3600, для прода 86400
        if (int(current_job_interval) != recieved_interval or
                job.misfire_grace_time != misfire_grace_time):
            next_run_time = getattr(job, 'next_run_time', None)
            if next_run_time:
                new_start_date = next_run_time + timedelta(minutes=int(recieved_interval))  # Для прода должно стоять days
            else:
                new_start_date = effective_start

            scheduler.modify_job(
                job_id,
                trigger=IntervalTrigger(minutes=recieved_interval,
                                        start_date=new_start_date),  # Для прода должно стоять days
                misfire_grace_time=misfire_grace_time
            )
            logger.info(
                f'🕒 {job_id} будет перезапущена с новым интервалом {recieved_interval} начиная с {new_start_date}, grace_time={misfire_grace_time}')
        else:
            logger.info(f'✅ {job_id} уже запланирована с интервалом {recieved_interval} и grace_time={misfire_grace_time}')
    else:
        scheduler.add_job(
            func,
            trigger=IntervalTrigger(minutes=recieved_interval,
                                    start_date=effective_start),  # Для прода должно стоять days
            id=job_id,
            replace_existing=True,
            misfire_grace_time=misfire_grace_time,
        )
        logger.info(f'🆕 {job_id} создана. Старт: {effective_start}')


async def schedule_pairing_jobs(session_maker):
    global current_interval

    async with session_maker() as session:
        result = await session.execute(
            select(Setting).where(Setting.id == 1))
        setting = result.scalar_one()

        setting_interval = setting.global_interval
        start_date = (
            setting.first_pairing_date
            if setting and setting.first_pairing_date
            else datetime.utcnow()
        )

        interval_for_job = setting_interval * 7

    if not scheduler.running:
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED)
        scheduler.start()

    if current_interval != setting_interval:
        logger.info(
            f'🔁 Интервал изменился: {current_interval} ➡️ {setting_interval}')
        current_interval = setting_interval

    start_date_for_auto_pairing = start_date
    schedule_or_reschedule('auto_pairing_weekly',
                           auto_pairing_wrapper,
                           interval_for_job,
                           session_maker,
                           start_date=start_date_for_auto_pairing,
                           misfire_grace_time=120)  # Для прода: misfire_grace_time=172800 (для теста 7200 - 2 часа)

    start_date_for_feedback_dispatcher = await schedule_feedback_dispatcher_for_auto_pairing(
        start_date_for_auto_pairing)

    schedule_or_reschedule('reload_jobs_checker',
                           reload_scheduled_wrapper,
                           1,
                           session_maker,
                           start_date=start_date_for_auto_pairing,
                           misfire_grace_time=60)  # Для прода: misfire_grace_time=86400 (для теста 3600 - 1 час)

    show_next_runs(scheduler)


async def reload_scheduled_jobs(session_maker):
    async with session_maker() as session:
        result = await session.execute(
            select(Setting.global_interval).where(Setting.id == 1))
        new_interval = result.scalar_one()

    global current_interval
    if current_interval != new_interval:
        logger.info(
            f'🔁 Интервал изменился: {current_interval} ➡️ {new_interval}')
        current_interval = new_interval

        await schedule_pairing_jobs(session_maker)
    else:
        logger.debug(
            '✅ Интервал не изменился. Задачи остаются с прежним интервалом.')
