"""Environment-driven settings shared by every service.

All services subclass :class:`BaseServiceSettings` and add their own fields.
Values come from environment variables prefixed with ``RAG_`` (or a local
``.env`` file during development), per twelve-factor configuration.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings for a RAG platform service.

    Attributes:
        service_name: Machine-readable service identifier (e.g. ``ingestion``).
        environment: Deployment environment name.
        log_level: Root log level (standard logging level names).
        host: Bind address for the HTTP server.
        port: Bind port for the HTTP server.
    """

    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    service_name: str = "service"
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def is_dev(self) -> bool:
        """Return True when running in the development environment."""
        return self.environment == "dev"
