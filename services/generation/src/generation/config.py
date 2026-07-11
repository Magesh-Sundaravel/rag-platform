"""Settings for the generation service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Generation Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "generation"
    port: int = 8004
