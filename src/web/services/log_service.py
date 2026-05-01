"""
Log service - Singleton pattern to ensure all components use the same instance.
"""

import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional


class LogService:
    """Log management service - thread-safe singleton."""

    _instance = None
    _instance_lock = threading.Lock()
    _main_loop = None  # 存储主事件循环引用

    def __new__(cls):
        # Double-checked locking so concurrent threads don't create duplicate
        # instances on cold-start.
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._initialized = False
                    cls._instance = inst
        return cls._instance

    def __init__(self):
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        self._logs: List[Dict] = []
        self._logs_lock = threading.Lock()
        self._websocket_connections: List = []
        self._ws_lock = threading.Lock()

    def set_event_loop(self, loop):
        """Set the main event loop for cross-thread communication."""
        LogService._main_loop = loop

    def add_log(self, log_type: str, message: str, data: Optional[Dict] = None):
        """Add log entry."""
        log_entry = {
            "type": log_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }
        with self._logs_lock:
            self._logs.append(log_entry)
            # Keep only last 1000 logs
            if len(self._logs) > 1000:
                del self._logs[:-1000]

        # Snapshot ws list under lock so we don't iterate while another thread mutates.
        with self._ws_lock:
            has_connections = bool(self._websocket_connections)

        if LogService._main_loop and has_connections:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_message({"event": "log", "data": log_entry}),
                    LogService._main_loop,
                )
            except Exception:
                # 静默失败，不影响主流程
                pass

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent logs."""
        with self._logs_lock:
            return list(self._logs[-limit:])

    def clear_logs(self):
        """Clear all logs."""
        with self._logs_lock:
            self._logs = []

    def add_websocket(self, websocket):
        """Add websocket connection."""
        with self._ws_lock:
            self._websocket_connections.append(websocket)

    def remove_websocket(self, websocket):
        """Remove websocket connection."""
        with self._ws_lock:
            if websocket in self._websocket_connections:
                self._websocket_connections.remove(websocket)

    async def _broadcast_message(self, message: dict):
        """Broadcast message to all connected websockets."""
        with self._ws_lock:
            connections = list(self._websocket_connections)

        disconnected = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        if disconnected:
            with self._ws_lock:
                for ws in disconnected:
                    if ws in self._websocket_connections:
                        self._websocket_connections.remove(ws)
