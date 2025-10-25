"""
Logs routes.
"""

from fastapi import APIRouter, Depends

from ..services.log_service import LogService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/logs", tags=["logs"])
log_service = LogService()


@router.get("")
async def get_logs(
    limit: int = 100,
    payload: dict = Depends(verify_token_dependency)
):
    """Get recent logs."""
    logs = log_service.get_recent_logs(limit)
    return {"status": "ok", "logs": logs}


