"""
API routers module.
"""

from .auth import router as auth_router
from .config import router as config_router
from .scan import router as scan_router
from .keys import router as keys_router
from .logs import router as logs_router
from .memory import router as memory_router
from .settings import router as settings_router
from .queries import router as queries_router
from .reports import router as reports_router

__all__ = [
    "auth_router",
    "config_router",
    "scan_router",
    "keys_router",
    "logs_router",
    "memory_router",
    "settings_router",
    "queries_router",
    "reports_router",
]


