"""
Scan memory management routes.
"""

from fastapi import APIRouter, HTTPException, Depends

from ..services.memory_service import MemoryService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/memory", tags=["memory"])
memory_service = MemoryService()


@router.get("/stats")
async def get_memory_stats(payload: dict = Depends(verify_token_dependency)):
    """Get scan memory statistics."""
    try:
        stats = memory_service.get_stats()
        return {"status": "ok", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_memory(payload: dict = Depends(verify_token_dependency)):
    """Clear all scan memory (processed queries and scanned files)."""
    try:
        memory_service.clear_memory()
        return {"status": "ok", "message": "Scan memory cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

