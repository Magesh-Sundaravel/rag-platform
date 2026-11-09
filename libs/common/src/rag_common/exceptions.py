"""Exception hierarchy shared across all platform services.

Every domain error raised inside a service should be (a subclass of)
:class:`RagPlatformError` so the app factory can render it as a consistent
JSON error envelope with the right HTTP status.
"""


class RagPlatformError(Exception):
    """Base class for all platform domain errors.

    Attributes:
        code: Stable machine-readable error code.
        status_code: HTTP status this error maps to at the API boundary.
        detail: Human-readable description of the failure.
    """

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, detail: str) -> None:
        """Store the human-readable detail message.

        Args:
            detail: Description of what went wrong.
        """
        super().__init__(detail)
        self.detail = detail


class NotFoundError(RagPlatformError):
    """A requested resource does not exist."""

    code = "not_found"
    status_code = 404


class InvalidInputError(RagPlatformError):
    """The request payload is semantically invalid."""

    code = "invalid_input"
    status_code = 422


class ConflictError(RagPlatformError):
    """The request conflicts with existing state (e.g. duplicate)."""

    code = "conflict"
    status_code = 409


class UpstreamError(RagPlatformError):
    """A dependency (database, LLM API, another service) failed."""

    code = "upstream_error"
    status_code = 502


class ServiceUnavailableError(RagPlatformError):
    """A dependency is temporarily unavailable; the client should retry."""

    code = "service_unavailable"
    status_code = 503
