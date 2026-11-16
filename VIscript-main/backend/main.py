import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings
from db.supabase_client import supabase_client
from db.chromadb_client import chromadb_client
from routers import (
    upload_router,
    transcripts_router,
    query_router,
    alerts_router,
    cameras_router,
    digest_router,
    auth_router,
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("visualiq")

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing VisualIQ V2.0 Enterprise Engine...")
    logger.info(f"Environment: {settings.APP_ENV} | Vision Provider: {settings.VISION_PROVIDER}")
    yield
    logger.info("Shutting down VisualIQ Engine...")

# Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="VisualIQ Surveillance Intelligence API",
    description="VLM-powered continuous video transcript generation and natural language query engine.",
    version="2.0.0",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration (FIX: operator precedence bug — parentheses required)
cors_origins = (settings.ALLOWED_ORIGINS + ["*"]) if settings.APP_ENV == "development" else settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.APP_ENV != "development":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Global Exception Handler — never leak internal details in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    detail = str(exc) if settings.APP_ENV == "development" else "An unexpected error occurred. Please try again later."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": detail,
            "path": request.url.path
        }
    )

# Health & Diagnostic Endpoint
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "service": "VisualIQ Intelligence Platform",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
        "vision_provider": settings.VISION_PROVIDER,
        "models": {
            "gemini_primary": settings.GEMINI_PRIMARY_MODEL,
            "groq_fallback": settings.GROQ_VISION_MODEL,
        }
    }

# Mount Routers under /api
app.include_router(upload_router, prefix="/api")
app.include_router(transcripts_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(cameras_router, prefix="/api")
app.include_router(digest_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=(settings.APP_ENV == "development"),
        reload_dirs=[str(backend_dir)] if settings.APP_ENV == "development" else None,
        reload_excludes=["*.jpg", "*.jpeg", "*.png", "*.mp4", "*.avi", "frames*", "uploads*"]
    )
