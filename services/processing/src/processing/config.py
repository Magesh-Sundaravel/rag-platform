"""Settings for the processing service."""

from typing import Literal

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Processing Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "processing"
    port: int = 8002
    database_url: str = "postgresql+asyncpg://rag:rag_dev_password@localhost:5432/rag"
    processing_queue_url: str = "http://localhost:9324/000000000000/rag-processing"
    sqs_endpoint_url: str | None = None
    queue_wait_seconds: int = 20
    max_receive_count: int = 3
    worker_enabled: bool = True
    chunk_strategy: Literal["fixed", "recursive"] = "recursive"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    embedding_provider: Literal["fake", "bedrock"] = "fake"
