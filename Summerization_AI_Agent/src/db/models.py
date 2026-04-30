"""SQLAlchemy ORM models for summarization service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from config import settings
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_SCHEMA = settings.db_schema


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    """Always return timezone-aware UTC datetime — never naive."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class SummaryConfig(Base):
    """Summarization template configurations."""

    __tablename__ = "summary_configs"
    __table_args__ = {"schema": _SCHEMA}

    id: Mapped[int | None] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    intent: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    min_words: Mapped[int] = mapped_column(Integer, nullable=False)
    max_words: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    style_hint: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(128))
    updated_by: Mapped[str | None] = mapped_column(String(128))
    deleted_by: Mapped[str | None] = mapped_column(String(128))
