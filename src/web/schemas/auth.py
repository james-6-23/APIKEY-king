"""
Authentication related schemas.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request model."""
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


