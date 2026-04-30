"""Pydantic schemas for Summarization & Narrative engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class OutputLanguage(StrEnum):
    en = "en"
    hi = "hi"
    pa = "pa"
    mr = "mr"


# ── Summarization request / response ─────────────────────────────────────────


class SummarizeRequest(BaseModel):
    text: str = Field(..., max_length=100_000)
    summary_type: str | None = Field(
        default=None,
        alias="summaryType",
        description=(
            "Key from summary_configs e.g. 'bullet_short', 'tldr'. Uses default if omitted."
        ),
    )
    language: OutputLanguage = OutputLanguage.en
    app_id: str | None = Field(default=None, alias="appId")

    model_config = {"populate_by_name": True}


class SummarizeResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    summary: str
    word_count: int
    summary_type: str
    label: str
    format: str
    model_used: str
    confidence_score: float = Field(
        description=(
            "0.0 to 1.0 — how well output matches expected summary config (word range, non-empty)."
        )
    )


# ── Summary type CRUD schemas ─────────────────────────────────────────────────


class SummaryTypeItem(BaseModel):
    """Read schema — returned by GET endpoints."""

    key: str
    label: str
    intent: str
    format: str
    min_words: int
    max_words: int
    instruction: str
    style_hint: str | None
    is_default: bool
    is_active: bool


class SummaryTypeCreate(BaseModel):
    """Write schema — used by POST /types."""

    key: str = Field(..., max_length=50, description="Unique identifier e.g. 'bullet_short'")
    label: str = Field(..., max_length=100, description="Human-readable label shown in UI")
    intent: str = Field(..., max_length=50, description="e.g. bullet, tldr, summary, narrative")
    format: str = Field(..., max_length=50, description="bullet | paragraph | structured | mixed")
    min_words: int = Field(..., ge=1)
    max_words: int = Field(..., ge=1)
    instruction: str = Field(..., description="Main prompt instruction sent to LLM")
    style_hint: str | None = Field(
        default=None, description="Optional tone hint e.g. 'formal', 'simple'"
    )
    is_default: bool = Field(default=False, description="Set true to make this the fallback type")
    is_active: bool = Field(default=True)

    model_config = {"populate_by_name": True}


class SummaryTypeUpdate(BaseModel):
    """Partial update schema — all fields optional for PUT /types/{key}."""

    label: str | None = Field(default=None, max_length=100)
    intent: str | None = Field(default=None, max_length=50)
    format: str | None = Field(default=None, max_length=50)
    min_words: int | None = Field(default=None, ge=1)
    max_words: int | None = Field(default=None, ge=1)
    instruction: str | None = None
    style_hint: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None
