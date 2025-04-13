from sqlalchemy import (Column, Integer,
                        String, ForeignKey,
                        Boolean, Interval,
                        DateTime, Date
                        )
from sqlalchemy.orm import relationship, sessionmaker, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from datetime import datetime

from db import Base, CommonMixin
from config import DATABASE_URL, engine


class Users(CommonMixin, Base):
    """Таблица пользователя."""

    telegram_id = Column(Integer)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_activate = Column(Boolean, default=False)
    is_in_group = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    pairing_interval = Column(Interval)
    last_paired_at = Column(DateTime)
    pause_until = Column(DateTime)
    joined_at = Column(DateTime, default=datetime.utcnow)

    pairs_as_user1 = relationship(
        "Pair", foreign_keys="[Pair.user1_id]", back_populates="user1"
        )
    pairs_as_user2 = relationship(
        "Pair", foreign_keys="[Pair.user2_id]", back_populates="user2"
        )
    feedbacks = relationship("Feedback", back_populates="user")


class Pairs(CommonMixin, Base):
    """Таблица пар."""

    user1_id = Column(Integer, ForeignKey('users.id'))
    user2_id = Column(Integer, ForeignKey('users.id'))

    paired_at = Column(DateTime)  # Изменено на DateTime для хранения времени
    feedback_status = Column(String)

    user1 = relationship(
        "User", foreign_keys=[user1_id], back_populates="pairs_as_user1"
        )
    user2 = relationship(
        "User", foreign_keys=[user2_id], back_populates="pairs_as_user2"
        )

    feedbacks = relationship("Feedback", back_populates="pair")


class Feedback(CommonMixin, Base):
    """Таблица с обратной связью."""

    pair_id = Column(Integer, ForeignKey('pairs.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    did_meet = Column(Boolean, default=False)
    comment = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    pair = relationship("Pair", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
    

class Common_interval(CommonMixin, Base):
    """Интервал между встречами."""
    
    number_of_day = Column(Integer)


# engine = create_engine(DATABASE_URL)

# SessionLocal = sessionmaker(bind=engine)


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Создание всех таблиц

if __name__ == "__main__":
   import asyncio
   asyncio.run(create_database())
