import itertools
from typing import Iterable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from random_coffee_bot.database.models import User, Pair

from random_coffee_bot.utils.pairing import generate_unique_pairs


async def create_users(session: AsyncSession, n: int) -> list[User]:
    """Создаёт n пользователей и возвращает их в порядке добавления."""
    users: list[User] = []
    for i in range(n):
        u = User(
            telegram_id=10_000 + i,
            username=f"user{i}",
            first_name=f"U{i}",
            last_name=None,
            is_active=True,
            has_permission=True,
        )
        session.add(u)
        users.append(u)
    await session.flush()
    return users


def as_unordered_pair_set(p: Pair) -> set[frozenset[int]]:
    """
    Представление пары/тройки в виде множества неориентированных пар.
    - Для пары: { {u1,u2} }
    - Для тройки: { {u1,u2}, {u1,u3}, {u2,u3} }
    """
    ids = [p.user1_id, p.user2_id] + ([p.user3_id] if p.user3_id else [])
    ids = [i for i in ids if i is not None]
    return {frozenset(c) for c in itertools.combinations(ids, 2)}


def round_to_pair_edges(pairs: Iterable[Pair]) -> set[frozenset[int]]:
    """Все рёбра-двойки (как неориентированные множества id) из раунда."""
    edges: set[frozenset[int]] = set()
    for p in pairs:
        edges |= as_unordered_pair_set(p)
    return edges


def has_exactly_one_triple(pairs: list[Pair]) -> bool:
    return sum(1 for p in pairs if p.user3_id is not None) == 1


def users_are_disjoint(pairs: list[Pair]) -> bool:
    """Каждый пользователь встречается не более 1 раза в раунде."""
    seen: set[int] = set()
    for p in pairs:
        ids = [p.user1_id, p.user2_id] + ([p.user3_id] if p.user3_id else [])
        for uid in ids:
            if uid in seen:
                return False
            seen.add(uid)
    return True


@pytest.mark.asyncio
async def test_even_count_produces_only_pairs_no_self_no_overlap(session: AsyncSession):
    users = await create_users(session, 6)
    new_pairs = await generate_unique_pairs(session, users)

    # только пары (без троек)
    assert all(p.user3_id is None for p in new_pairs), "При чётном N не должно быть троек"

    # нет самопар
    assert all(p.user1_id != p.user2_id for p in new_pairs), "Самопары недопустимы"

    # пользователи не пересекаются между парами
    assert users_are_disjoint(new_pairs), "Пользователь не должен встречаться более одного раза в раунде"

    # граф раунда покрывает всех пользователей
    involved = set()
    for p in new_pairs:
        involved.update([p.user1_id, p.user2_id])
    assert len(involved) == len(users), "Все пользователи должны быть задействованы"


@pytest.mark.asyncio
async def test_odd_count_has_exactly_one_triple_and_no_overlap(session: AsyncSession):
    users = await create_users(session, 7)
    new_pairs = await generate_unique_pairs(session, users)

    assert has_exactly_one_triple(new_pairs), "Должна быть ровно одна тройка"
    assert users_are_disjoint(new_pairs), "Никто не должен повторяться в рамках раунда"

    # граф раунда покрывает всех пользователей
    involved = set()
    for p in new_pairs:
        ids = [p.user1_id, p.user2_id] + ([p.user3_id] if p.user3_id else [])
        involved.update(ids)
    assert len(involved) == len(users), "Все пользователи должны быть задействованы"


@pytest.mark.asyncio
async def test_uniqueness_against_previous_round_pairs_even_case(session: AsyncSession):
    """
    Проверяем, что при наличии прошлых пар функция старается избежать их повторения.
    previous_edges: пары прошлого раунда
    new_edges: пары текущего раунда (внутри троек тоже разложены на рёбра)
    """
    users = await create_users(session, 6)

    # Сымитируем прошлый раунд: (u1,u2), (u3,u4), (u5,u6)
    u1, u2, u3, u4, u5, u6 = users
    prev = [
        Pair(user1_id=u1.id, user2_id=u2.id),
        Pair(user1_id=u3.id, user2_id=u4.id),
        Pair(user1_id=u5.id, user2_id=u6.id),
    ]
    for p in prev:
        session.add(p)
    await session.flush()

    previous_edges = round_to_pair_edges(prev)

    new_pairs = await generate_unique_pairs(session, users)
    new_edges = round_to_pair_edges(new_pairs)

    # никакая пара не должна совпасть с уже существовавшей
    assert previous_edges.isdisjoint(new_edges), (
        f"Обнаружено повторение пары: {previous_edges & new_edges}"
    )

    # sanity-check: формат текущего раунда валиден
    assert users_are_disjoint(new_pairs)


@pytest.mark.asyncio
async def test_uniqueness_against_previous_round_pairs_odd_case(session: AsyncSession):
    """
    Нечётный случай: прошлого раунда тоже избегаем.
    Важно: если в новом раунде получилась тройка, то все 3 её ребра (u1,u2), (u1,u3), (u2,u3)
    не должны совпасть с прошлым набором пар.
    """
    users = await create_users(session, 7)

    # Прошлый раунд (все пары):
    prev_pairs = []
    for a, b in zip(users[::2], users[1::2]):  # (0,1), (2,3), (4,5) — седьмой останется вне
        p = Pair(user1_id=a.id, user2_id=b.id)
        prev_pairs.append(p)
        session.add(p)
    await session.flush()

    previous_edges = round_to_pair_edges(prev_pairs)

    new_pairs = await generate_unique_pairs(session, users)
    new_edges = round_to_pair_edges(new_pairs)

    assert previous_edges.isdisjoint(new_edges), (
        f"Обнаружено повторение прошлой пары (включая рёбра тройки): {previous_edges & new_edges}"
    )
    assert has_exactly_one_triple(new_pairs)
    assert users_are_disjoint(new_pairs)


@pytest.mark.asyncio
async def test_uniqueness_against_twq_previous_rounds_pairs_even_case(session: AsyncSession):
    """
    Проверяем, что при наличии прошлых пар функция старается избежать их повторения.
    previous_edges: пары прошлого раунда
    new_edges: пары текущего раунда (внутри троек тоже разложены на рёбра)
    """
    users = await create_users(session, 6)

    # Сымитируем прошлый раунд: (u1,u2), (u3,u4), (u5,u6)
    u1, u2, u3, u4, u5, u6 = users
    prev = [
        Pair(user1_id=u1.id, user2_id=u2.id),
        Pair(user1_id=u3.id, user2_id=u4.id),
        Pair(user1_id=u5.id, user2_id=u6.id),
        Pair(user1_id=u1.id, user2_id=u3.id),
        Pair(user1_id=u2.id, user2_id=u5.id),
        Pair(user1_id=u4.id, user2_id=u6.id),
    ]
    for p in prev:
        session.add(p)
    await session.flush()

    previous_edges = round_to_pair_edges(prev)

    new_pairs = await generate_unique_pairs(session, users)
    new_edges = round_to_pair_edges(new_pairs)

    # никакая пара не должна совпасть с уже существовавшей
    assert previous_edges.isdisjoint(new_edges), (
        f"Обнаружено повторение пары: {previous_edges & new_edges}"
    )

    # sanity-check: формат текущего раунда валиден
    assert users_are_disjoint(new_pairs)
