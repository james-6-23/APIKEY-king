"""
FastAPI web server for APIKEY-king visualization.
Main application entry point.
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .routers import (
    auth_router,
    config_router,
    scan_router,
    keys_router,
    logs_router,
    memory_router,
    settings_router,
    queries_router,
    reports_router,
)
from .websocket import websocket_logs_router

# Create FastAPI app
app = FastAPI(
    title="APIKEY-king",
    description="API Key Discovery Tool with Web Interface",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {"name": "auth", "description": "认证相关接口"},
        {"name": "config", "description": "配置管理接口"},
        {"name": "scan", "description": "扫描控制接口"},
        {"name": "keys", "description": "密钥管理接口"},
        {"name": "logs", "description": "日志查询接口"},
        {"name": "memory", "description": "扫描记忆管理接口"},
        {"name": "settings", "description": "系统设置接口"},
        {"name": "queries", "description": "查询规则管理接口"},
    ]
)

# Lightweight security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add basic security-related headers."""

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "accelerometer=(), camera=(), microphone=()")
        return response

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)

allowed_origins = [origin.strip() for origin in os.getenv("APIKEY_KING_CORS", "*").split(",") if origin.strip()]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(config_router)
app.include_router(scan_router)
app.include_router(keys_router)
app.include_router(logs_router)
app.include_router(memory_router)
app.include_router(settings_router)
app.include_router(queries_router)
app.include_router(reports_router)

# Include WebSocket router
app.include_router(websocket_logs_router)

# Health check endpoint (must be before static files mount)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "APIKEY-king"}

# Static files (frontend) - must be last
app.mount("/", StaticFiles(directory="web", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
