"""
Scan related schemas.
"""

from pydantic import BaseModel


class ScanControlRequest(BaseModel):
    """Scan control request model."""
    action: str  # start or stop


