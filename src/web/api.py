"""
FastAPI web server for APIKEY-king visualization.
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    auth_router,
    config_router,
    scan_router,
    keys_router,
    logs_router,
    memory_router,
    settings_router,
    queries_router,
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Include WebSocket router
app.include_router(websocket_logs_router)

# Static files (frontend)
app.mount("/", StaticFiles(directory="web", html=True), name="static")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "APIKEY-king"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
