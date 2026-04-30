"""
Summarization & Narrative routes.

── Summarization ──────────────────────────────────────────────
POST /api/v1/summarize

── Summary Type Management (CRUD) ────────────────────────────
GET    /api/v1/summarize/types
GET    /api/v1/summarize/types/all
GET    /api/v1/summarize/types/{key}
POST   /api/v1/summarize/types
PUT    /api/v1/summarize/types/{key}
DELETE /api/v1/summarize/types/{key}
"""

from __future__ import annotations

import asyncpg
import structlog
from config.auth import verify_token
from db.session import get_pool
from fastapi import APIRouter, Depends, HTTPException, Response, status
from schemas.summarize_schemas import (
    SummarizeRequest,
    SummarizeResponse,
    SummaryTypeCreate,
    SummaryTypeItem,
    SummaryTypeUpdate,
)
from services.prompt_store import PromptStore
from services.summarization_engine import SummarizationEngine

logger = structlog.get_logger()
router = APIRouter(dependencies=[Depends(verify_token)])


def _pool() -> asyncpg.Pool:
    return get_pool()


# ── Summarization ─────────────────────────────────────────────────────────────


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Summarize text",
    description="Pass `summaryType` key to choose style. Omit to use default.",
)
async def summarize(
    body: SummarizeRequest,
    pool: asyncpg.Pool = Depends(_pool),
) -> SummarizeResponse:
    try:
        return await SummarizationEngine(pool).summarize(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error("summarize_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summarization failed",
        )


# ── Summary Type — List ───────────────────────────────────────────────────────


@router.get(
    "/summarize/types",
    response_model=list[SummaryTypeItem],
    status_code=status.HTTP_200_OK,
    summary="List active summary types",
)
async def list_summary_types(
    pool: asyncpg.Pool = Depends(_pool),
) -> list[SummaryTypeItem]:
    rows = await PromptStore(pool).list_active()
    return [SummaryTypeItem(**r) for r in rows]


@router.get(
    "/summarize/types/all",
    response_model=list[SummaryTypeItem],
    status_code=status.HTTP_200_OK,
    summary="List all summary types including inactive",
)
async def list_all_summary_types(
    pool: asyncpg.Pool = Depends(_pool),
) -> list[SummaryTypeItem]:
    rows = await PromptStore(pool).list_all()
    return [SummaryTypeItem(**r) for r in rows]


# ── Summary Type — Get single ─────────────────────────────────────────────────


@router.get(
    "/summarize/types/{key}",
    response_model=SummaryTypeItem,
    status_code=status.HTTP_200_OK,
    summary="Get a single summary type by key",
)
async def get_summary_type(
    key: str,
    pool: asyncpg.Pool = Depends(_pool),
) -> SummaryTypeItem:
    row = await PromptStore(pool).get_by_key(key)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary type '{key}' not found.",
        )
    return SummaryTypeItem(**row)


# ── Summary Type — Create ─────────────────────────────────────────────────────


@router.post(
    "/summarize/types",
    response_model=SummaryTypeItem,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new summary type",
    description="Set `is_default: true` to make it the fallback when no type is specified.",
)
async def create_summary_type(
    body: SummaryTypeCreate,
    pool: asyncpg.Pool = Depends(_pool),
) -> SummaryTypeItem:
    try:
        row = await PromptStore(pool).create(body)
        return SummaryTypeItem(**row)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        logger.error("create_summary_type_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create summary type",
        )


# ── Summary Type — Update ─────────────────────────────────────────────────────


@router.put(
    "/summarize/types/{key}",
    response_model=SummaryTypeItem,
    status_code=status.HTTP_200_OK,
    summary="Update an existing summary type",
    description="Partial update — only send fields you want to change.",
)
async def update_summary_type(
    key: str,
    body: SummaryTypeUpdate,
    pool: asyncpg.Pool = Depends(_pool),
) -> SummaryTypeItem:
    try:
        row = await PromptStore(pool).update(key, body)
        return SummaryTypeItem(**row)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("update_summary_type_failed", key=key, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update summary type",
        )


# ── Summary Type — Delete ─────────────────────────────────────────────────────


@router.delete(
    "/summarize/types/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a summary type",
    description="Cannot delete the default type — reassign default first.",
)
async def delete_summary_type(
    key: str,
    pool: asyncpg.Pool = Depends(_pool),
) -> Response:
    try:
        await PromptStore(pool).delete(key)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("delete_summary_type_failed", key=key, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete summary type",
        )
