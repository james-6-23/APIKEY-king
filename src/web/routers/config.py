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

    # 不要掩码 tokens，因为前端需要完整的 token 来重新填充表单
    # 用户已经通过 JWT 认证，可以安全地返回完整配置

    return {"status": "ok", "config": config}


