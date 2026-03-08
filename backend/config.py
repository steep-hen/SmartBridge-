"""
Configuration management for AI Financial Advisor backend.

Loads environment variables from .env file and provides type-validated
configuration through Pydantic settings.

Usage:
    from backend.config import settings
    db_url = settings.database_url
"""

import logging
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Raises:
        ValidationError: If required environment variables are missing
                        or invalid types.
    """

    # Application Configuration
    debug: bool = True
    environment: str = "development"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Database Configuration
    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/ai_advisor_dev"
    )
    postgres_url: Optional[str] = None  # Alias for database_url

    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data):
        """Initialize settings and validate on startup."""
        super().__init__(**data)
        self._setup_logging()

    @property
    def db_url(self) -> str:
        """
        Get database URL with fallback support.
        
        Returns:
            str: PostgreSQL connection URL
        """
        return self.postgres_url or self.database_url

    def _setup_logging(self) -> None:
        """Configure logging at module level based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Singleton instance of settings
settings = Settings()

if settings.debug:
    logger = logging.getLogger(__name__)
    logger.debug(f"Loaded settings from environment (env={settings.environment})")
