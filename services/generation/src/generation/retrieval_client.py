"""HTTP client for the retrieval service's hybrid search endpoint."""

import asyncio

import httpx

from rag_common.exceptions import UpstreamError
from rag_contracts.search import SearchRequest, SearchResponse

# Exponential backoff base delay between retries, in seconds.
_BACKOFF_SECONDS = 0.5


class RetrievalClient:
    """Calls the retrieval service's ``POST /search`` over HTTP."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        retries: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure the client.

        Args:
            base_url: Retrieval service base URL (e.g. ``http://localhost:8003``).
            timeout: Per-request timeout, in seconds.
            retries: Number of retries after the first attempt, on 5xx or
                transport errors.
            transport: Optional transport override (tests inject a mock).
        """
        self._base_url = base_url
        self._timeout = timeout
        self._retries = retries
        self._transport = transport

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Run a hybrid search query against the retrieval service.

        Args:
            request: The search request to send.

        Returns:
            The fused, ranked search results.

        Raises:
            UpstreamError: If every attempt fails (5xx or transport error).
        """
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            base_url=self._base_url, timeout=self._timeout, transport=self._transport
        ) as client:
            for attempt in range(self._retries + 1):
                if attempt > 0:
                    await asyncio.sleep(_BACKOFF_SECONDS * attempt)
                try:
                    response = await client.post("/search", json=request.model_dump(mode="json"))
                except httpx.TransportError as exc:
                    last_error = exc
                    continue
                if response.status_code >= 500:
                    last_error = UpstreamError(f"retrieval service returned {response.status_code}")
                    continue
                response.raise_for_status()
                return SearchResponse.model_validate(response.json())
        attempts = self._retries + 1
        raise UpstreamError(
            f"retrieval service unreachable after {attempts} attempts"
        ) from last_error
