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
    
    # 设置主事件循环（首次连接时）
    import asyncio
    log_service.set_event_loop(asyncio.get_running_loop())
    
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


