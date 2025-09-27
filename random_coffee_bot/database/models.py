from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, DateTime,
                        Date, Integer, ForeignKey, func, String, Text)
from sqlalchemy.orm import (DeclarativeBase,
                            declared_attr,
                            Mapped,
                            mapped_column,
                            relationship)


class Base(DeclarativeBase):
    pass


class CommonMixin:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class User(CommonMixin, Base):
    """Таблица пользователя."""

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True,
                                             nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True,
                                            nullable=False)
    has_permission: Mapped[bool] = mapped_column(Boolean, default=True,
                                                 nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False,
                                             nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False,
                                           nullable=False)

    pairing_interval: Mapped[int | None] = mapped_column(Integer,
                                                         nullable=True)
    last_paired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    pause_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    pairs_as_user1: Mapped[list['Pair']] = relationship(
        'Pair',
        foreign_keys='Pair.user1_id',
        back_populates='user1'
    )
    pairs_as_user2: Mapped[list['Pair']] = relationship(
        'Pair',
        foreign_keys='Pair.user2_id',
        back_populates='user2'
    )
    pairs_as_user3: Mapped[list['Pair']] = relationship(
        'Pair',
        foreign_keys='Pair.user3_id',
        back_populates='user3'
    )


class Pair(CommonMixin, Base):
    """Таблица пар."""

    user1_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey('user.id'),
                                          nullable=False)
    user2_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey('user.id'),
                                          nullable=False)
    user3_id: Mapped[int | None] = mapped_column(Integer,
                                                 ForeignKey('user.id'),
                                                 nullable=True)

    user1: Mapped[User] = relationship(
        'User', foreign_keys=[user1_id], back_populates='pairs_as_user1'
    )
    user2: Mapped[User] = relationship(
        'User', foreign_keys=[user2_id], back_populates='pairs_as_user2'
    )
    user3: Mapped[User | None] = relationship(
        'User', foreign_keys=[user3_id], back_populates='pairs_as_user3'
    )


class Setting(CommonMixin, Base):
    """Таблица для изменяемых настроек работы бота."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    global_interval: Mapped[int] = mapped_column(Integer, nullable=False,
                                                 default=2)
    first_pairing_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False)
    is_pairing_on: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                                default=False)

    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('id = 1', name='settings_singleton'),
    )


class Notification(CommonMixin, Base):
    """Таблица для текстов рассылки от админа."""

    text: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
                                                     nullable=True)
