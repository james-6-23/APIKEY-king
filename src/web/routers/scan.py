"""
Scan control routes.
"""

from fastapi import APIRouter, HTTPException, Depends

from ..schemas.scan import ScanControlRequest
from ..services.scan_service import ScanService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/scan", tags=["scan"])
scan_service = ScanService()


@router.post("/control")
async def control_scan(
    request: ScanControlRequest,
    payload: dict = Depends(verify_token_dependency)
):
    """Start, stop, pause or resume scanning."""
    try:
        if request.action == "start":
            result = scan_service.start_scan()
            return result
        elif request.action == "stop":
            result = scan_service.stop_scan()
            return result
        elif request.action == "pause":
            result = scan_service.pause_scan()
            return result
        elif request.action == "resume":
            result = scan_service.resume_scan()
            return result
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_scan_status(payload: dict = Depends(verify_token_dependency)):
    """Get scanner status."""
    status = scan_service.get_status()
    return {"status": "ok", **status}


