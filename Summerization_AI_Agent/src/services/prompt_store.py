"""DB access layer for summary_configs.
Uses asyncpg directly — no ORM.
"""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg
import structlog
from config import settings
from schemas.summarize_schemas import SummaryTypeCreate, SummaryTypeUpdate

logger = structlog.get_logger()

_LANG_MAP: dict[str, str] = {
    "en": "Respond in English.",
    "hi": "Respond in Hindi (Devanagari script).",
    "pa": "Respond in Punjabi (Gurmukhi script).",
    "mr": "Respond in Marathi (Devanagari script).",
}


class PromptStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._table = f"{settings.db_schema}.summary_configs"

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_config(self, key: str) -> dict:
        row = await self._pool.fetchrow(
            f"SELECT * FROM {self._table} WHERE key = $1 AND is_active = TRUE", key
        )
        if row is None:
            raise ValueError(f"Summary type '{key}' not found or inactive.")
        return dict(row)

    async def get_by_key(self, key: str) -> dict | None:
        row = await self._pool.fetchrow(f"SELECT * FROM {self._table} WHERE key = $1", key)
        return dict(row) if row else None

    async def get_default_config(self) -> dict:
        row = await self._pool.fetchrow(
            f"SELECT * FROM {self._table} WHERE is_default = TRUE AND is_active = TRUE"
        )
        if row is None:
            raise ValueError("No default summary type configured in DB.")
        return dict(row)

    async def list_active(self) -> list[dict]:
        rows = await self._pool.fetch(
            f"SELECT * FROM {self._table} WHERE is_active = TRUE ORDER BY id"
        )
        return [dict(r) for r in rows]

    async def list_all(self) -> list[dict]:
        rows = await self._pool.fetch(f"SELECT * FROM {self._table} ORDER BY id")
        return [dict(r) for r in rows]

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, data: SummaryTypeCreate) -> dict:
        existing = await self.get_by_key(data.key)
        if existing:
            raise ValueError(f"Summary type '{data.key}' already exists.")

        if data.is_default:
            await self._clear_default()

        now = datetime.now(UTC)
        row = await self._pool.fetchrow(
            f"""
            INSERT INTO {self._table}
                (key, label, intent, format, min_words, max_words,
                 instruction, style_hint, is_default, is_active,
                 created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            RETURNING *
            """,
            data.key,
            data.label,
            data.intent,
            data.format,
            data.min_words,
            data.max_words,
            data.instruction,
            data.style_hint,
            data.is_default,
            data.is_active,
            now,
            now,
        )
        logger.info("summary_type_created", key=data.key)
        return dict(row)

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, key: str, data: SummaryTypeUpdate) -> dict:
        existing = await self.get_by_key(key)
        if existing is None:
            raise ValueError(f"Summary type '{key}' not found.")

        if data.is_default is True:
            await self._clear_default()

        fields = data.model_dump(exclude_none=True)
        if not fields:
            return existing

        fields["updated_at"] = datetime.now(UTC)

        set_clause = ", ".join(f"{col} = ${i + 2}" for i, col in enumerate(fields.keys()))
        values = list(fields.values())

        row = await self._pool.fetchrow(
            f"UPDATE {self._table} SET {set_clause} WHERE key = $1 RETURNING *",
            key,
            *values,
        )
        logger.info("summary_type_updated", key=key, fields=list(fields.keys()))
        return dict(row)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, key: str) -> None:
        existing = await self.get_by_key(key)
        if existing is None:
            raise ValueError(f"Summary type '{key}' not found.")
        if existing["is_default"]:
            raise ValueError(
                f"Cannot delete '{key}' — it is the default type. "
                "Set another type as default first."
            )
        await self._pool.execute(f"DELETE FROM {self._table} WHERE key = $1", key)
        logger.info("summary_type_deleted", key=key)

    # ── Helper ────────────────────────────────────────────────────────────────

    async def _clear_default(self) -> None:
        await self._pool.execute(
            f"UPDATE {self._table} SET is_default = FALSE, updated_at = $1 WHERE is_default = TRUE",
            datetime.now(UTC),
        )

    # ── Prompt builder ────────────────────────────────────────────────────────

    @staticmethod
    def build_system_prompt(config: dict, language: str) -> str:
        parts = [
            config["instruction"],
            f"Response must be between {config['min_words']} and {config['max_words']} words.",
        ]
        if config.get("style_hint"):
            parts.append(f"Tone: {config['style_hint']}.")
        parts.append(_LANG_MAP.get(language, "Respond in English."))
        return "\n".join(parts)
