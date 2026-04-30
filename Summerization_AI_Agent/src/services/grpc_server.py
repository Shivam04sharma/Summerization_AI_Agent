"""gRPC server — runs alongside FastAPI."""

from __future__ import annotations

import grpc
import structlog
from config import settings
from grpc_reflection.v1alpha import reflection
from services.grpc_summarize_service import SummarizeServiceImpl
from summarize.v1 import summarize_service_pb2 as pb2
from summarize.v1 import summarize_service_pb2_grpc as pb2_grpc

logger = structlog.get_logger()

_server: grpc.aio.Server | None = None


async def start_grpc_server() -> None:
    global _server

    port = getattr(settings, "grpc_port", 50053)
    _server = grpc.aio.server()
    pb2_grpc.add_SummarizeServiceServicer_to_server(SummarizeServiceImpl(), _server)

    service_names = (
        pb2.DESCRIPTOR.services_by_name["SummarizeService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, _server)

    _server.add_insecure_port(f"[::]:{port}")
    await _server.start()

    logger.info("grpc_server_started", port=port)


async def stop_grpc_server() -> None:
    global _server
    if _server:
        await _server.stop(grace=5)
        logger.info("grpc_server_stopped")
        _server = None
