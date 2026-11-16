import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("visualiq.config")

try:
    from dotenv import load_dotenv
    has_dotenv = True
except ImportError:
    has_dotenv = False

# Load .env file from project root or backend folder
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    if has_dotenv:
        load_dotenv(dotenv_path=env_path)
    else:
        # Pure-python .env loader fallback
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
elif has_dotenv:
    load_dotenv()


class Settings:
    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",") if origin.strip()
    ]
    PORT: int = int(os.getenv("PORT", "8000"))

    # AI Model Selection & Providers (2026 Standard)
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "gemini").lower()
    
    # Gemini (Primary 2026)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PRIMARY_MODEL: str = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.8-flash")
    GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")

    # Groq (Secondary Vision & Text Fallback)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "llama-3.3-70b-versatile")
    GROQ_TEXT_MODEL: str = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")

    # Local Ollama Fallback (Dev-only, zero cost on local GPU)
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

    # Supabase (PostgreSQL 16 + Auth + Storage)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Vector Store
    CHROMADB_URL: str = os.getenv("CHROMADB_URL", "http://localhost:8001")
    CHROMADB_COLLECTION: str = os.getenv("CHROMADB_COLLECTION", "visualiq_transcripts")
    USE_SUPABASE_VECTOR: bool = os.getenv("USE_SUPABASE_VECTOR", "false").lower() in ("true", "1", "yes")

    # Redis (Job Status & Event Bus)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Video & Ingestion Parameters
    FRAME_SAMPLE_FPS: float = float(os.getenv("FRAME_SAMPLE_FPS", "0.2"))  # 1 frame per 5 seconds
    MOTION_THRESHOLD: float = float(os.getenv("MOTION_THRESHOLD", "0.08"))  # 8% pixel difference
    MAX_BURST_FRAMES: int = int(os.getenv("MAX_BURST_FRAMES", "5"))
    ANOMALY_ALERT_THRESHOLD: int = int(os.getenv("ANOMALY_ALERT_THRESHOLD", "6"))

    # Directory Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR.parent / "uploads"
    FRAMES_DIR: Path = BASE_DIR.parent / "frames"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod", "staging")


def _validate_production_config(s: Settings):
    """Fail fast if critical production configuration is missing."""
    errors: list[str] = []

    if not s.SECRET_KEY or len(s.SECRET_KEY) < 32:
        errors.append(
            "SECRET_KEY must be set to a strong random string (>= 32 chars) in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )

    if not s.SUPABASE_URL or s.SUPABASE_URL.startswith("https://your-"):
        errors.append("SUPABASE_URL must be configured with your real Supabase project URL.")

    if not s.SUPABASE_SERVICE_ROLE_KEY or s.SUPABASE_SERVICE_ROLE_KEY.startswith("your-"):
        errors.append("SUPABASE_SERVICE_ROLE_KEY must be set to your Supabase service role key.")

    if not s.GEMINI_API_KEY and not s.GROQ_API_KEY:
        errors.append("At least one AI provider key (GEMINI_API_KEY or GROQ_API_KEY) must be configured.")

    if errors:
        logger.critical("=" * 60)
        logger.critical("FATAL: Production configuration validation failed!")
        logger.critical("=" * 60)
        for err in errors:
            logger.critical(f"  • {err}")
        logger.critical("=" * 60)
        sys.exit(1)


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Validate in production mode
if settings.is_production:
    _validate_production_config(settings)
elif not settings.SECRET_KEY:
    # In development, auto-generate a random key if not set
    import secrets
    settings.SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("SECRET_KEY not set — generated ephemeral key for development. Set SECRET_KEY in .env for persistence.")
