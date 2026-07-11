"""ASGI entrypoint for the retrieval service."""

from rag_common.app_factory import create_app
from retrieval import __version__
from retrieval.config import Settings

settings = Settings()
app = create_app(settings, title="Retrieval Service", version=__version__)
