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
)
from .websocket import websocket_logs_router

# Create FastAPI app
app = FastAPI(
    title="APIKEY-king",
    description="API Key Discovery Tool with Web Interface",
    version="1.0.0"
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
