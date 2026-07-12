"""ASGI entrypoint for the ingestion service."""

from ingestion import __version__
from ingestion.config import Settings
from ingestion.routes import router
from rag_common.app_factory import create_app

settings = Settings()
app = create_app(settings, title="Ingestion Service", version=__version__)
app.include_router(router)
