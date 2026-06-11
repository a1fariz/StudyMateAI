"""
StudyMate AI - FastAPI Application Entry Point.

A RAG-powered study assistant that helps students learn from their documents.
Features: JWT auth, PDF processing, semantic search, RAG chat, AI generators.
"""

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.database import init_db
from backend.routers import auth, documents, search, chat, features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ──────────────────────────────────────
# Simple in-memory rate limiter
# ──────────────────────────────────────
class RateLimiter:
    """Token-bucket style rate limiter keyed by client IP."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Prune old entries
        self._hits[client_ip] = [
            t for t in self._hits[client_ip] if now - t < self.window
        ]
        if len(self._hits[client_ip]) >= self.max_requests:
            return False
        self._hits[client_ip].append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # ── Startup ──
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Validate critical configuration
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        logger.warning("⚠️  GEMINI_API_KEY is not set. AI features will be unavailable.")
    else:
        logger.info("✅ Gemini API key configured")

    await init_db()
    logger.info("✅ Database initialized")

    # Create required directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"📁 Upload directory: {settings.UPLOAD_DIR}")

    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    logger.info(f"🧠 ChromaDB directory: {settings.CHROMA_PERSIST_DIR}")

    logger.info(f"🔒 Rate limit: {settings.RATE_LIMIT_PER_MINUTE} req/min")
    logger.info(f"🌐 CORS origins: {settings.ALLOWED_ORIGINS}")
    logger.info("=" * 50)
    logger.info(f"✨ {settings.APP_NAME} v{settings.APP_VERSION} is ready!")
    logger.info("=" * 50)

    yield

    # ── Shutdown ──
    logger.info(f"👋 Shutting down {settings.APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🎓 StudyMate AI — An intelligent study assistant powered by RAG "
        "(Retrieval-Augmented Generation). Upload your study materials, "
        "ask questions, generate summaries, quizzes, flashcards, and study plans. "
        "Built with FastAPI, ChromaDB, Sentence-Transformers, and Google Gemini."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    license_info={"name": "MIT License"},
    contact={"name": "StudyMate AI", "url": "https://github.com/studymate-ai"},
)


# ──────────────────────────────────────
# Middleware
# ──────────────────────────────────────

# CORS middleware
origins = (
    settings.ALLOWED_ORIGINS.split(",")
    if settings.ALLOWED_ORIGINS != "*"
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to API endpoints."""
    # Skip rate limiting for static files and docs
    if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security-hardening headers to all responses."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ──────────────────────────────────────
# Health Check Endpoint
# ──────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    """
    Returns application health status.
    Used by Docker, load balancers, and monitoring systems.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ──────────────────────────────────────
# API Routers
# ──────────────────────────────────────
from fastapi.staticfiles import StaticFiles

app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(features.router, prefix="/api/v1")

# Serve frontend static assets (compiled SPA in dist, or raw source in dev) at the root
frontend_dir = "frontend/dist" if os.path.exists("frontend/dist") else "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

