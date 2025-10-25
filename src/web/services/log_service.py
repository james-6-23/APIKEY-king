"""
Log service - Singleton pattern to ensure all components use the same instance.
"""

from datetime import datetime
from typing import Dict, List, Optional
import asyncio


class LogService:
    """Log management service - Singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._logs = []
        self._websocket_connections = []
    
    def add_log(self, log_type: str, message: str, data: Optional[Dict] = None):
        """Add log entry."""
        log_entry = {
            "type": log_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        self._logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self._logs) > 1000:
            self._logs = self._logs[-1000:]
        
        # Broadcast to websockets (sync version)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._broadcast_message({
                    "event": "log",
                    "data": log_entry
                }))
        except:
            pass  # Skip if no event loop
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent logs."""
        return self._logs[-limit:]
    
    def clear_logs(self):
        """Clear all logs."""
        self._logs = []
    
    def add_websocket(self, websocket):
        """Add websocket connection."""
        self._websocket_connections.append(websocket)
    
    def remove_websocket(self, websocket):
        """Remove websocket connection."""
        if websocket in self._websocket_connections:
            self._websocket_connections.remove(websocket)
    
    async def _broadcast_message(self, message: dict):
        """Broadcast message to all connected websockets."""
        disconnected = []
        for ws in self._websocket_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.remove_websocket(ws)


