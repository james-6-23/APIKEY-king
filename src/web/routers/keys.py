"""
API keys management routes.
"""

from fastapi import APIRouter, HTTPException, Depends

from ..services.key_service import KeyService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/keys", tags=["keys"])
key_service = KeyService()


@router.get("")
async def get_keys(payload: dict = Depends(verify_token_dependency)):
    """Get discovered keys."""
    try:
        keys_data = key_service.get_all_keys()
        return {
            "status": "ok",
            "keys": keys_data,
            "total": len(keys_data)
        }
    except Exception as e:
        return {
            "status": "error",
            "keys": [],
            "total": 0,
            "message": str(e)
        }


@router.delete("/clear")
async def clear_keys(payload: dict = Depends(verify_token_dependency)):
    """Clear all discovered keys."""
    try:
        key_service.clear_all_keys()
        return {"status": "ok", "message": "Keys cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


