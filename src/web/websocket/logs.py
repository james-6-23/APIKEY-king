"""
WebSocket handler for real-time logs.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.log_service import LogService

router = APIRouter()
log_service = LogService()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time logs."""
    await websocket.accept()
    log_service.add_websocket(websocket)
    
    try:
        # Send recent logs
        await websocket.send_json({
            "event": "history",
            "data": log_service.get_recent_logs(50)
        })
        
        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        log_service.remove_websocket(websocket)


