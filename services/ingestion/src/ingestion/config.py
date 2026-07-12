"""Settings for the ingestion service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Ingestion Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "ingestion"
    port: int = 8001
    database_url: str = "postgresql+asyncpg://rag:rag_dev_password@localhost:5432/rag"
