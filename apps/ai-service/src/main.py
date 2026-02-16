"""
ProjectForge AI Service
Main application with RAG, embeddings, chat, and AI copilot
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import close_db, init_db

# Import routers
from .chat.router import router as chat_router
from .copilot.router import router as copilot_router
from .documents.router import router as documents_router
from .rag.router import router as rag_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info("Starting AI Service...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down AI Service...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="ProjectForge AI Service",
    description="AI service for RAG, embeddings, chat, and project copilot features",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else None,
        },
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ProjectForge AI Service",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Include routers with API prefix
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(rag_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(copilot_router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
