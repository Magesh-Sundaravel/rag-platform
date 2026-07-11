"""Settings for the retrieval service."""

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Retrieval Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "retrieval"
    port: int = 8003
