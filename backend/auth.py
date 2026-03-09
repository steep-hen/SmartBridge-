"""
Authentication and authorization module.

Provides API key authentication for protected endpoints.
Uses X-API-KEY header for client authentication.

Usage:
    from fastapi import Depends
    from backend.auth import get_api_key
    
    @app.post("/protected")
    async def protected_endpoint(api_key: str = Depends(get_api_key)):
        # api_key is valid
        return {"message": "authenticated"}
"""

from fastapi import HTTPException, Header, status
from backend.config import settings


async def get_api_key(x_api_key: str = Header(None)) -> str:
    """
    Validate API key from X-API-KEY header.
    
    Args:
        x_api_key: API key from request header
    
    Returns:
        str: The validated API key
    
    Raises:
        HTTPException: 401 Unauthorized if key is missing or invalid
        
    Example:
        >>> # Valid request with header: X-API-KEY: secret-key-value
        >>> key = await get_api_key(x_api_key="secret-key-value")
        
        >>> # Missing header
        >>> key = await get_api_key(x_api_key=None)  # Raises 401
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing. Include X-API-KEY header in request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Compare with configured secret key
    if x_api_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return x_api_key


async def verify_api_key(api_key: str = Header(None, alias="X-API-KEY")) -> bool:
    """
    Verify API key without returning it.
    
    Useful for routes that don't need to use the key itself.
    
    Args:
        api_key: API key from X-API-KEY header
    
    Returns:
        bool: True if key is valid
    
    Raises:
        HTTPException: 401 Unauthorized if key is invalid
    """
    if not api_key or api_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return True
