import logging
import random
from collections import defaultdict
from datetime import datetime, UTC

from aiogram import Bot
from sqlalchemy import select, func, or_, cast, Date, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import User, Pair, Setting
from ..services.admin_service import notify_users_about_pairs


logger = logging.getLogger(__name__)


async def get_users_ready_for_pairing(session: AsyncSession) -> list['User']:
    """
    Отбирает всех юзеров готовых для формирования пар.

    У таких юзеров:
    - статус Активен (is_activa == True);
    - они не на паузе, либо дата окончания паузы уже прошла (
        pause_until == Null or pause_until < today);
    - прошло достаточно времени с их последней встречи (
        задан личном интервале: today - pairing_interval <= last_paired_at,
        не задан: today - global_interval <= last_paired_at).
    """

    setting_result = await session.execute(
        select(Setting.global_interval).where(Setting.id == 1))
    global_interval_weeks = setting_result.scalar_one()

    today_date = cast(func.timezone('UTC', func.now()), Date)
    coalesced_weeks = func.coalesce(User.pairing_interval,
                                    bindparam('global_weeks'))
    threshold_datetime = (func.timezone('UTC', func.now())
                          - func.make_interval(0, 0, coalesced_weeks))
    threshold_date = cast(threshold_datetime, Date)

    stmt = (
        select(User).where(
            User.is_active.is_(True),
            or_(User.pause_until.is_(None), User.pause_until <= today_date),
            or_(User.last_paired_at.is_(None),
                cast(User.last_paired_at, Date) <= threshold_date))
    )

    users_result = await session.execute(
        stmt, {'global_weeks': global_interval_weeks})
    return list(users_result.scalars().all())


async def generate_unique_pairs(session, users: list[User]) -> list[Pair]:
    """Формирует пары, минимизируя количество повторений."""

    result = await session.execute(
        select(Pair.user1_id, Pair.user2_id, Pair.user3_id))
    history = defaultdict(int)  # (min_id, max_id) -> count

    for row in result.fetchall():
        ids = [row.user1_id, row.user2_id]
        if row.user3_id:
            ids.append(row.user3_id)
        ids = sorted(ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                history[(ids[i], ids[j])] += 1

    random.shuffle(users)
    user_ids = [u.id for u in users]
    user_map = {u.id: u for u in users}
    used = set()
    pairs = []

    possible_pairs = []
    for i in range(len(user_ids)):
        for j in range(i + 1, len(user_ids)):
            u1, u2 = user_ids[i], user_ids[j]
            key = tuple(sorted((u1, u2)))
            if u1 not in used and u2 not in used:
                possible_pairs.append((history[key], u1, u2))

    possible_pairs.sort()

    for _, u1, u2 in possible_pairs:
        if u1 not in used and u2 not in used:
            used.update([u1, u2])
            pairs.append((u1, u2))

    remaining = [uid for uid in user_ids if uid not in used]
    pair_objs = []

    for u1_id, u2_id in pairs:
        u1, u2 = user_map[u1_id], user_map[u2_id]
        pair = Pair(
            user1_id=u1.id, user2_id=u2.id
        )
        u1.last_paired_at = datetime.now(UTC)
        u2.last_paired_at = datetime.now(UTC)
        session.add(pair)
        pair_objs.append(pair)

    if remaining:
        odd = user_map[remaining[0]]
        odd.last_paired_at = datetime.now(UTC)
        if pair_objs:
            last_pair = pair_objs[-1]
            last_pair.user3_id = odd.id
            session.add(last_pair)
        else:
            logger.info(f'⚠️ Один пользователь остался без пары: {odd.id}')

    return pair_objs


async def auto_pairing(session_maker, bot: Bot):
    async with session_maker() as session:
        users = await get_users_ready_for_pairing(session)
        logger.info(f'Юзеры, готовые к парингу: {users}')

        if len(users) < 2:
            logger.info('❗ Недостаточно пользователей для формирования пар.')
            return

        pairs = await generate_unique_pairs(session, users)

        await session.commit()
        logger.info(f'✅ Сформировано {len(pairs)} пар.')

        await notify_users_about_pairs(session, pairs, bot)
