"""ASGI entrypoint for the generation service."""

from generation import __version__
from generation.config import Settings
from generation.routes import router
from rag_common.app_factory import create_app

settings = Settings()
app = create_app(settings, title="Generation Service", version=__version__)
app.include_router(router)
