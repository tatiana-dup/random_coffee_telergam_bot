import logging
import random
from collections import defaultdict
from datetime import datetime

from aiogram import Bot
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Pair, Setting
from services.admin_service import notify_users_about_pairs

logger = logging.getLogger(__name__)


async def get_users_ready_for_matching(session: AsyncSession) -> list[User]:
    """Выбираем пользователей для участия в формировании пар по правилам."""

    result = await session.execute(select(Setting)
                                   .filter_by(key='global_interval'))
    setting = result.scalars().first()
    global_interval = setting.value if setting else 2

    result = await session.execute(select(User))
    users = result.scalars().all()
    selected_users = []
    today = datetime.utcnow().date()

    for user in users:
        if user.pause_until and user.pause_until > today:
            continue

        user_interval = user.pairing_interval or global_interval

        if not user.is_active:
            if user_interval > global_interval and user.future_meeting == 0:
                user.future_meeting = 1
            continue

        if global_interval >= user_interval:
            user.future_meeting = 0
            selected_users.append(user)
        elif user.future_meeting == 1:
            user.future_meeting = 0
            selected_users.append(user)
        else:
            user.future_meeting = 1

    await session.commit()
    return selected_users


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
            user1_id=u1.id, user2_id=u2.id,
            paired_at=datetime.utcnow()
        )
        u1.last_paired_at = datetime.utcnow()
        u2.last_paired_at = datetime.utcnow()
        session.add(pair)
        pair_objs.append(pair)

    if remaining:
        odd = user_map[remaining[0]]
        odd.last_paired_at = datetime.utcnow()
        if pair_objs:
            last_pair = pair_objs[-1]
            last_pair.user3_id = odd.id
            session.add(last_pair)
        else:
            logger.info(f'⚠️ Один пользователь остался без пары: {odd.id}')

    return pair_objs


async def auto_pairing(session_maker, bot: Bot):
    async with session_maker() as session:
        users = await get_users_ready_for_matching(session)
        if len(users) < 2:
            logger.info('❗ Недостаточно пользователей для формирования пар.')
            return

        pairs = await generate_unique_pairs(session, users)

        await session.commit()
        logger.info(f'✅ Сформировано {len(pairs)} пар.')

        await notify_users_about_pairs(session, pairs, bot)
