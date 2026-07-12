"""Settings for the retrieval service."""

from typing import Literal

from rag_common.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Retrieval Service settings; see BaseServiceSettings for env conventions."""

    service_name: str = "retrieval"
    port: int = 8003
    database_url: str = "postgresql+asyncpg://rag:rag_dev_password@localhost:5432/rag"
    embedding_provider: Literal["fake", "gemini"] = "fake"
