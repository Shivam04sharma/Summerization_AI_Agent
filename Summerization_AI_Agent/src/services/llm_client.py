"""
LLM client for the Summarization & Narrative engine.

Provider selected from settings.intent_router_provider:
  "gemini"  → Vertex AI
  "openai"  → OpenAI

To add a new provider: subclass BaseLLMClient, implement complete(),
then add it to LLMClientFactory._REGISTRY.
"""

from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from datetime import UTC

import structlog
from config import settings

logger = structlog.get_logger()


def _strip_fences(text: str) -> str:
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def _get_langfuse():
    if not settings.langfuse_enabled:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as exc:
        logger.warning("langfuse_init_failed", error=str(exc))
        return None


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        """Return raw text from the LLM."""

    async def complete_json(
        self, system: str, user: str, temperature: float, max_tokens: int
    ) -> dict:
        raw = await self.complete(system, user, temperature, max_tokens)
        try:
            return json.loads(_strip_fences(raw))
        except json.JSONDecodeError as exc:
            logger.warning("llm_json_parse_failed", error=str(exc), raw=raw[:300])
            raise ValueError(f"LLM returned non-JSON response: {raw[:200]}") from exc

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier used in API responses."""


class GeminiClient(BaseLLMClient):
    @property
    def model_name(self) -> str:
        return f"gemini/{settings.gemini_model}"

    async def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        import json
        import tempfile

        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        credentials_info = {
            "type": "service_account",
            "project_id": settings.vertex_ai_project_id,
            "private_key_id": settings.gcp_private_key_id,
            "private_key": settings.gcp_private_key.replace("\\n", "\n"),
            "client_email": settings.gcp_client_email,
            "client_id": settings.gcp_client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_info, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name

        vertexai.init(
            project=settings.vertex_ai_project_id,
            location=settings.vertex_ai_location,
        )
        model = GenerativeModel(settings.gemini_model)
        config = GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)

        def _call() -> str:
            import time
            from datetime import datetime

            start = datetime.now(UTC)
            t0 = time.time()
            contents = [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}]
            response = model.generate_content(contents, generation_config=config)
            text = response.text or ""

            lf = _get_langfuse()
            if lf:
                try:
                    usage = {}
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        u = response.usage_metadata
                        usage = {
                            "input": u.prompt_token_count,
                            "output": u.candidates_token_count,
                            "total": u.total_token_count,
                            "unit": "TOKENS",
                        }
                    trace = lf.trace(
                        name="Summarization",
                        metadata={"service": settings.service_name},
                    )
                    trace.generation(
                        name="gemini-generate",
                        model=settings.gemini_model,
                        start_time=start,
                        end_time=datetime.now(UTC),
                        input=user,
                        output=text,
                        usage=usage,
                        metadata={"response_time": round(time.time() - t0, 3)},
                    )
                    lf.flush()
                except Exception as exc:
                    logger.warning("langfuse_trace_error", error=str(exc))

            return text

        return await asyncio.to_thread(_call)


class OpenAIClient(BaseLLMClient):
    @property
    def model_name(self) -> str:
        return f"openai/{settings.openai_model}"

    async def complete(self, system: str, user: str, temperature: float, max_tokens: int) -> str:
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        try:
            resp = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except openai.RateLimitError as exc:
            logger.warning(
                "openai_quota_exceeded_falling_back_to_gemini",
                error=str(exc),
            )
            return await GeminiClient().complete(system, user, temperature, max_tokens)

        text = resp.choices[0].message.content or ""

        lf = _get_langfuse()
        if lf:
            try:
                from datetime import datetime

                trace = lf.trace(
                    name="Summarization",
                    metadata={"service": settings.service_name},
                )
                trace.generation(
                    name="openai-generate",
                    model=settings.openai_model,
                    end_time=datetime.now(UTC),
                    input=user,
                    output=text,
                    usage={
                        "input": resp.usage.prompt_tokens,  # type: ignore[union-attr]
                        "output": resp.usage.completion_tokens,  # type: ignore[union-attr]
                        "total": resp.usage.total_tokens,  # type: ignore[union-attr]
                        "unit": "TOKENS",
                    },
                )
                lf.flush()
            except Exception as exc:
                logger.warning("langfuse_trace_error", error=str(exc))

        return text


class LLMClientFactory:
    """
    Returns the correct LLM client from settings.intent_router_provider.
    Add new providers by registering them in _REGISTRY.
    """

    _REGISTRY: dict[str, type[BaseLLMClient]] = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
    }

    @classmethod
    def create(cls) -> BaseLLMClient:
        provider = settings.intent_router_provider.lower()
        client_cls = cls._REGISTRY.get(provider)
        if client_cls is None:
            raise ValueError(
                f"Unknown LLM provider '{provider}'. "
                f"Supported: {list(cls._REGISTRY.keys())}. "
                "Check INTENT_ROUTER_PROVIDER in your .env file."
            )
        return client_cls()
