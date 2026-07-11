"""Settings for the ingestion service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Ingestion Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "ingestion"
    port: int = 8001
