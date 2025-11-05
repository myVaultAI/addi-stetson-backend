"""
DME-CPH Backend API
FastAPI application for DME-CPH demo system
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.ollama import router as ollama_router
from routers.dashboard import router as dashboard_router
from routers.rag import router as rag_router
from routers.voice import router as voice_router
from routers.webhooks import router as webhooks_router
import uvicorn
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DME-CPH Backend API",
    description="Backend API for DME-CPH demo system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for production and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://addi.vaultailab.com",  # Production frontend
        "http://localhost:41000",        # Local development
        "http://localhost:3000"          # OpenWebUI
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ollama_router)
app.include_router(dashboard_router)
app.include_router(rag_router)
app.include_router(voice_router)
app.include_router(webhooks_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DME-CPH Backend",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DME-CPH Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# API status endpoint
@app.get("/api/status")
async def api_status():
    """API status with service information"""
    return {
        "api_status": "operational",
        "services": {
            "ollama": "localhost:40000",
            "openwebui": "localhost:41000",
            "backend": "localhost:44000"
        },
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=44000,
        reload=True,
        log_level="info"
    )
