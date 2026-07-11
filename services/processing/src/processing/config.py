"""Settings for the processing service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Processing Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "processing"
    port: int = 8002
