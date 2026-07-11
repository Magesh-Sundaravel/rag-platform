"""Structured logging setup shared by all services.

JSON logs in staging/prod (machine-ingestible), pretty console logs in dev.
Stdlib logging is routed through structlog so third-party library logs share
the same format.
"""

import logging

import structlog

from rag_common.config import BaseServiceSettings


def configure_logging(settings: BaseServiceSettings) -> None:
    """Configure structlog and stdlib logging for a service.

    Args:
        settings: The service settings; ``log_level`` and ``environment``
            drive verbosity and output format.
    """
    level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    renderer: structlog.typing.Processor = (
        structlog.dev.ConsoleRenderer() if settings.is_dev else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=level, format="%(message)s")


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    """Return a bound structlog logger for the given component name.

    Args:
        name: Logger name, typically the module path.

    Returns:
        A structlog bound logger.
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
