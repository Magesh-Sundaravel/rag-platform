"""ASGI entrypoint for the processing service."""

from processing import __version__
from processing.config import Settings
from rag_common.app_factory import create_app

settings = Settings()
app = create_app(settings, title="Processing Service", version=__version__)
