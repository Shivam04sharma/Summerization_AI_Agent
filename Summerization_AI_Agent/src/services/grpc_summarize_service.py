"""gRPC SummarizeService implementation.

Receives SummarizeRequest via gRPC, calls SummarizationEngine, returns SummarizeResponse.
"""

from __future__ import annotations

import grpc
import structlog
from db.session import get_pool
from schemas.summarize_schemas import SummarizeRequest as PydanticRequest
from services.summarization_engine import SummarizationEngine
from summarize.v1 import summarize_service_pb2 as pb2
from summarize.v1 import summarize_service_pb2_grpc as pb2_grpc

logger = structlog.get_logger()


class SummarizeServiceImpl(pb2_grpc.SummarizeServiceServicer):
    """gRPC handler for SummarizeService.Summarize RPC."""

    async def Summarize(self, request, context):
        logger.info(
            "grpc_summarize_request",
            summary_type=request.summary_type,
            language=request.language,
            text_length=len(request.text),
        )

        try:
            pool = get_pool()
            req = PydanticRequest(
                text=request.text,
                summary_type=request.summary_type or None,
                language=request.language or "en",
                app_id=request.app_id or None,
            )

            result = await SummarizationEngine(pool).summarize(req)

            logger.info(
                "grpc_summarize_response",
                word_count=result.word_count,
                confidence_score=result.confidence_score,
            )

            return pb2.SummarizeResponse(
                summary=result.summary,
                word_count=result.word_count,
                summary_type=result.summary_type,
                label=result.label,
                format=result.format,
                model_used=result.model_used,
                confidence_score=result.confidence_score,
            )

        except Exception as exc:
            logger.error("grpc_summarize_failed", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
