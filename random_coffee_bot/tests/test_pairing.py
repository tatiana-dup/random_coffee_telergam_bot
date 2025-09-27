from datetime import timedelta

import pytest

from random_coffee_bot.database.models import User, Setting
from random_coffee_bot.utils.pairing import get_users_ready_for_pairing


@pytest.mark.asyncio
async def test_includes_active_not_paused_never_paired(ensure_setting,
                                                       session):
    """
    Тест проверяет, что активный пользователь, у которого не задана пауза и
    для которого еще ни разу не была подобрана пара, попадает в выборку.
    """
    u = User(
        telegram_id=1,
        is_active=True,
        has_permission=True,
        is_blocked=False,
        is_admin=False,
        pairing_interval=None,
        last_paired_at=None,
        pause_until=None,
    )
    session.add(u)
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 1 in ids


@pytest.mark.asyncio
async def test_excludes_inactive(ensure_setting, session):
    """
    Тест проверяет, что неактивный пользователь не попадает в выборку.
    """
    u = User(
        telegram_id=2,
        is_active=False,
        pause_until=None,
        last_paired_at=None,
    )
    session.add(u)
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 2 not in ids


@pytest.mark.asyncio
async def test_excludes_if_paused_until_today_or_future(ensure_setting,
                                                        session,
                                                        utc_today):
    """
    Тест проверяет, что пользователь, который находится на паузе, т.е
    pause_until >= today, не попадает в выборку.
    """
    u_today = User(
        telegram_id=3,
        is_active=True,
        pause_until=utc_today,
        last_paired_at=None,
    )
    u_future = User(
        telegram_id=4,
        is_active=True,
        pause_until=utc_today + timedelta(days=1),
        last_paired_at=None,
    )
    session.add_all([u_today, u_future])
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 3 not in ids
    assert 4 not in ids


@pytest.mark.asyncio
async def test_includes_if_pause_is_past(ensure_setting, session, utc_today):
    """
    Тест проверяет, что активный пользователь, у которого закончилась пауза,
    т.е pause_until < today, попадает в выборку.
    """
    u = User(
        telegram_id=5,
        is_active=True,
        pause_until=utc_today - timedelta(days=1),
        last_paired_at=None,
    )
    session.add(u)
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 5 in ids


@pytest.mark.asyncio
async def test_global_interval_applies_when_no_personal_interval(
        ensure_setting, session, utc_today):
    """
    Тест проверяет, что для пользователя, у которого не указан личный
    интервал (pairing_interval=None), используется глобальный
    интервал (Setting.global_interval) и пользователь попадает в выборку,
    только если прошло достаточно времени с его последней встречи
    last_paired_at <= (today - global_interval_weeks).
    """
    setting = await session.get(Setting, 1)
    setting.global_interval = 3
    await session.flush()

    u_ok = User(
        telegram_id=6,
        is_active=True,
        pairing_interval=None,
        last_paired_at=utc_today - timedelta(weeks=4),
        pause_until=None,
    )
    u_not = User(
        telegram_id=7,
        is_active=True,
        pairing_interval=None,
        last_paired_at=utc_today - timedelta(weeks=2),
        pause_until=None,
    )
    session.add_all([u_ok, u_not])
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 6 in ids
    assert 7 not in ids


@pytest.mark.asyncio
async def test_personal_interval_overrides_global(ensure_setting,
                                                  session,
                                                  utc_today):
    """
    Тест проверяет, что пользователь, у которого указан личный
    интервал (pairing_interval), попадает в выборку,
    только если прошло достаточно времени с его последней встречи
    last_paired_at <= (today - pairing_interval).
    """
    setting = await session.get(Setting, 1)
    setting.global_interval = 3
    await session.flush()

    u_ok = User(
        telegram_id=8,
        is_active=True,
        pairing_interval=2,
        last_paired_at=utc_today - timedelta(weeks=3),
        pause_until=None,
    )

    u_not = User(
        telegram_id=9,
        is_active=True,
        pairing_interval=4,
        last_paired_at=utc_today - timedelta(weeks=3),
        pause_until=None,
    )
    session.add_all([u_ok, u_not])
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 8 in ids
    assert 9 not in ids


@pytest.mark.asyncio
async def test_last_paired_none_always_ok_if_other_filters_pass(
        ensure_setting, session):
    """
    Тест проверяет, что пользователь, у которого еще не было
    ни с кем сформировано пары, попадает в выборку
    (если активен и не на паузе).
    """
    u = User(
        telegram_id=10,
        is_active=True,
        pairing_interval=4,
        last_paired_at=None,
        pause_until=None,
    )
    session.add(u)
    await session.flush()

    users = await get_users_ready_for_pairing(session)
    ids = [x.telegram_id for x in users]
    assert 10 in ids
