"""Summerization_AI_Agent — Text Summarization & Narrative Service."""

import socket
from contextlib import asynccontextmanager

import structlog
import uvicorn
from config import settings
from db.session import close_db, init_db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.summarize_routes import router as summarization_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    try:
        from services.grpc_server import start_grpc_server, stop_grpc_server
        await start_grpc_server()
    except Exception as exc:
        logger.warning("grpc_server_start_failed", error=str(exc))

    logger.info(
        "startup",
        service=settings.service_name,
        env=settings.env,
        port=settings.port,
        provider=settings.intent_router_provider,
    )
    yield

    try:
        from services.grpc_server import stop_grpc_server
        await stop_grpc_server()
    except Exception:
        pass
    await close_db()
    logger.info("shutdown", service=settings.service_name)


app = FastAPI(
    title="Summerization_AI_Agent",
    version="1.0.0",
    description="AI-powered text summarization and narrative generation powered by Gemini (Vertex AI) or OpenAI.",
    lifespan=lifespan,
    root_path="/summarization",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


app.include_router(summarization_router, prefix="/api/v1", tags=["summarization"])


@app.get("/health", tags=["health"])
@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": app.version,
        "env": settings.env,
        "app_instance": socket.gethostname(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)



