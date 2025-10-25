"""
Scan reports routes.
"""

from fastapi import APIRouter, HTTPException, Depends

from ..services.report_service import ReportService
from ..services.auth_service import verify_token_dependency

router = APIRouter(prefix="/api/reports", tags=["reports"])
report_service = ReportService()


@router.get("")
async def get_reports(
    limit: int = 20,
    payload: dict = Depends(verify_token_dependency)
):
    """Get all scan reports."""
    try:
        reports = report_service.get_all_reports(limit)
        return {"status": "ok", "reports": reports, "total": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}")
async def get_report(
    report_id: int,
    payload: dict = Depends(verify_token_dependency)
):
    """Get a specific report."""
    try:
        report = report_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"status": "ok", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    payload: dict = Depends(verify_token_dependency)
):
    """Delete a scan report."""
    try:
        report_service.delete_report(report_id)
        return {"status": "ok", "message": "Report deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def clear_reports(payload: dict = Depends(verify_token_dependency)):
    """Clear all scan reports."""
    try:
        report_service.clear_all_reports()
        return {"status": "ok", "message": "All reports cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

