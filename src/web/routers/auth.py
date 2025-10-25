"""
Authentication routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..schemas.auth import LoginRequest, TokenResponse
from ..services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint."""
    if not auth_service.verify_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    access_token = auth_service.create_access_token({"sub": "admin"})
    return TokenResponse(access_token=access_token)


@router.get("/verify")
async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token."""
    payload = auth_service.verify_token(credentials.credentials)
    return {"status": "ok", "user": payload.get("sub")}


