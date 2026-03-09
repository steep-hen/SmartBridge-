"""
FastAPI application entry point.

Initializes the FastAPI application with all middleware, routes,
and exception handlers. This is the main ASGI application.

Usage:
    # Run with uvicorn
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    
    # Or import for testing
    from backend.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db import close_db
from backend.routes import health, users, reports, ai

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    
    Startup:
        - Initialize connections
        - Load configuration
        
    Shutdown:
        - Close database connections
        - Clean up resources
    """
    # Startup
    logger.info(f"Starting AI Financial Advisor API ({settings.environment})")
    logger.info(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    logger.info("Shutting down AI Financial Advisor API")
    close_db()


# Create FastAPI application
app = FastAPI(
    title="AI Financial Advisor API",
    description="Production-grade API for financial advisory services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware Configuration
# Restrict origins in production
origins = [
    "http://localhost:3000",      # Frontend dev server
    "http://localhost:8501",      # Streamlit dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8501",
]

if not settings.debug:
    # In production, add specific allowed origins
    origins = [
        "https://yourdomain.com",  # Update with actual domain
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(ai.router)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API metadata
    """
    return {
        "name": "AI Financial Advisor API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/version", tags=["info"])
async def version():
    """
    API version endpoint.
    
    Returns:
        dict: Version information
    """
    return {"version": "1.0.0", "environment": settings.environment}


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    Logs exceptions and returns safe error response to client.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "detail": "Internal server error",
        "error_id": id(exc),  # For log correlation
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
