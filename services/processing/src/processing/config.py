"""Settings for the processing service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Processing Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "processing"
    port: int = 8002
    database_url: str = "postgresql+asyncpg://rag:rag_dev_password@localhost:5432/rag"
    poll_interval_seconds: float = 1.0
    worker_enabled: bool = True
