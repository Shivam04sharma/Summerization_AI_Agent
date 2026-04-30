"""
SummarizationEngine — core business logic.
Uses asyncpg pool via PromptStore.
"""

from __future__ import annotations

import asyncpg
import structlog
from config import settings
from schemas.summarize_schemas import SummarizeRequest, SummarizeResponse
from services.llm_client import BaseLLMClient, LLMClientFactory
from services.prompt_store import PromptStore

logger = structlog.get_logger()


def _confidence_score(output: str, input_text: str, min_words: int, max_words: int) -> float:
    """
    Heuristic confidence score (0.0 – 1.0).

    Factors:
      - output_words in [min_words, max_words]  → 0.6 weight
      - compression ratio reasonable (0.05–0.9) → 0.4 weight
    """
    output_words = len(output.split())
    input_words = len(input_text.split())

    if output_words == 0:
        return 0.0

    # Word count score — full marks if within range, partial if outside
    if min_words <= output_words <= max_words:
        word_score = 1.0
    elif output_words < min_words:
        word_score = output_words / min_words
    else:
        word_score = max_words / output_words

    # Compression ratio score — summary should be shorter than input
    ratio = output_words / max(input_words, 1)
    if 0.05 <= ratio <= 0.9:
        ratio_score = 1.0
    elif ratio < 0.05:
        ratio_score = ratio / 0.05
    else:
        ratio_score = 0.2  # output longer than input — bad

    return round(word_score * 0.6 + ratio_score * 0.4, 2)


class SummarizationEngine:
    def __init__(self, pool: asyncpg.Pool, llm: BaseLLMClient | None = None) -> None:
        self._pool = pool
        self._llm = llm or LLMClientFactory.create()

    async def summarize(self, req: SummarizeRequest) -> SummarizeResponse:
        store = PromptStore(self._pool)

        config = (
            await store.get_config(req.summary_type)
            if req.summary_type
            else await store.get_default_config()
        )

        system = PromptStore.build_system_prompt(config, req.language.value)

        result = await self._llm.complete(
            system=system,
            user=req.text,
            temperature=settings.summarization_temperature,
            max_tokens=settings.summarization_max_output_tokens,
        )

        word_count = len(result.split())
        score = _confidence_score(result, req.text, config["min_words"], config["max_words"])

        logger.info(
            "summarize_completed",
            key=config["key"],
            intent=config["intent"],
            words=word_count,
            confidence_score=score,
        )

        return SummarizeResponse(
            summary=result,
            word_count=word_count,
            summary_type=config["key"],
            label=config["label"],
            format=config["format"],
            model_used=self._llm.model_name,
            confidence_score=score,
        )
