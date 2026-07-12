"""Settings for the generation service."""

from typing import Literal

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Generation Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "generation"
    port: int = 8004
    retrieval_url: str = "http://localhost:8003"
    generation_provider: Literal["fake", "gemini"] = "fake"
    request_timeout_seconds: float = 10.0
    retrieval_retries: int = 2
