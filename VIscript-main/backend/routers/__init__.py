from .upload import router as upload_router
from .transcripts import router as transcripts_router
from .query import router as query_router
from .alerts import router as alerts_router
from .cameras import router as cameras_router
from .digest import router as digest_router
from .auth import router as auth_router

__all__ = [
    "upload_router",
    "transcripts_router",
    "query_router",
    "alerts_router",
    "cameras_router",
    "digest_router",
    "auth_router",
]
