"""
Configuration routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials

from ..schemas.config import ConfigRequest
from ..services.config_service import ConfigService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/config", tags=["config"])
config_service = ConfigService()


@router.post("")
async def update_config(
    request: ConfigRequest,
    payload: dict = Depends(verify_token_dependency)
):
    """Update scanner configuration."""
    try:
        config_service.save_config(request)
        return {"status": "ok", "message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_config(payload: dict = Depends(verify_token_dependency)):
    """Get current configuration."""
    config = config_service.get_config()
    
    if not config:
        return {"status": "empty", "config": None}
    
    # Mask tokens for security
    config["github_tokens"] = [f"{t[:8]}..." for t in config.get("github_tokens", [])]
    
    return {"status": "ok", "config": config}


