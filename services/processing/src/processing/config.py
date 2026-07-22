"""Settings for the processing service."""

from typing import Literal

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Processing Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "processing"
    port: int = 8002
    database_url: str = "postgresql+asyncpg://rag:rag_dev_password@localhost:5432/rag"
    poll_interval_seconds: float = 1.0
    worker_enabled: bool = True
    chunk_strategy: Literal["fixed", "recursive"] = "recursive"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    embedding_provider: Literal["fake", "bedrock"] = "fake"
