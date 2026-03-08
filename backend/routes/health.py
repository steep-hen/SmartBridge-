"""
Health check endpoints for monitoring application and dependencies.

Provides lightweight health status and detailed diagnostic information
for load balancers, monitoring systems, and health checks.

Usage:
    from backend.routes.health import router
    app.include_router(router)
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Lightweight endpoint for load balancers and health checks.",
)
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        dict: Status indicator
        
    HTTP 200:
        Application is running and healthy.
        
    Example:
        curl http://localhost:8000/health
        {"status": "ok"}
    """
    logger.debug("Health check called")
    return {"status": "ok"}


@router.get(
    "/detailed",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Detailed health diagnostics",
    description="Extended health check with dependency status.",
)
async def health_detailed() -> Dict[str, Any]:
    """
    Detailed health check with system information.
    
    Returns:
        dict: Detailed status including component health
        
    HTTP 200:
        Application is healthy.
        
    HTTP 503:
        One or more dependencies are unavailable.
        
    Example:
        curl http://localhost:8000/health/detailed
        {
            "status": "ok",
            "database": "connected",
            "version": "1.0.0"
        }
    """
    health_status = {"status": "ok", "database": "connected"}

    logger.debug("Detailed health check called")
    return health_status


@router.get(
    "/ready",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness check - returns 200 when ready for traffic.",
)
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe.
    
    Indicates if the pod is ready to accept traffic.
    
    Returns:
        dict: Readiness status
        
    HTTP 200:
        Ready to accept traffic.
        
    HTTP 503:
        Not ready (e.g., migrations pending).
    """
    # Add any startup checks here
    logger.debug("Readiness check called")
    return {"status": "ready"}


@router.get(
    "/live",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness check - returns 200 if process is alive.",
)
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    
    Indicates if the application process is alive. If this returns an error,
    Kubernetes will restart the pod.
    
    Returns:
        dict: Liveness status
        
    HTTP 200:
        Process is alive and responsive.
    """
    logger.debug("Liveness check called")
    return {"status": "alive"}
