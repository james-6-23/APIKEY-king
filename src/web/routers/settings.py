"""
System settings routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..services.auth_service import AuthService, verify_token_dependency

router = APIRouter(prefix="/api/settings", tags=["settings"])
auth_service = AuthService()


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    old_password: str
    new_password: str


@router.get("/first-run")
async def check_first_run():
    """Check if this is the first run."""
    is_first = auth_service.is_first_run()
    return {"is_first_run": is_first}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    payload: dict = Depends(verify_token_dependency)
):
    """Change password."""
    success = auth_service.change_password(request.old_password, request.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid old password")
    
    return {"status": "ok", "message": "Password changed successfully"}

