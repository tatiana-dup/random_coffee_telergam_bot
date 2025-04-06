from sqlalchemy import (Column, Integer,
                        String, ForeignKey,
                        Boolean, Interval,
                        DateTime, Date
                        )
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Таблица пользователя."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
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


class Pair(Base):
    """Таблица пар."""

    __tablename__ = 'pairs'

    id = Column(Integer, primary_key=True)
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


class Feedback(Base):
    """Таблица с обратной связью."""

    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    pair_id = Column(Integer, ForeignKey('pairs.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    did_meet = Column(Boolean, default=False)
    comment = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    pair = relationship("Pair", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")


DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def create_database():
    try:
        Base.metadata.create_all(bind=engine)
        print("База данных и таблицы созданы.")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")


if __name__ == "__main__":
   create_database()