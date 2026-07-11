"""ASGI entrypoint for the ingestion service."""

from ingestion import __version__
from ingestion.config import Settings
from rag_common.app_factory import create_app

settings = Settings()
app = create_app(settings, title="Ingestion Service", version=__version__)
