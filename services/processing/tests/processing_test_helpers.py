"""Helpers for processing tests (unique module name repo-wide)."""

import uuid
from collections.abc import Sequence
from typing import Any


class FakeSqs:
    """Minimal in-memory SQS: messages stay until deleted; receive count grows."""

    def __init__(self) -> None:
        self.messages: dict[str, dict[str, Any]] = {}
        self.deleted: list[str] = []
        self.fail_next_receive: Exception | None = None

    def put(self, body: str) -> str:
        handle = uuid.uuid4().hex
        self.messages[handle] = {"Body": body, "ReceiptHandle": handle, "count": 0}
        return handle

    def receive_message(self, **_kwargs: Any) -> dict[str, Any]:
        if self.fail_next_receive is not None:
            error, self.fail_next_receive = self.fail_next_receive, None
            raise error
        for msg in self.messages.values():
            msg["count"] += 1
            return {
                "Messages": [
                    {
                        "Body": msg["Body"],
                        "ReceiptHandle": msg["ReceiptHandle"],
                        "Attributes": {"ApproximateReceiveCount": str(msg["count"])},
                    }
                ]
            }
        return {}

    def delete_message(self, *, QueueUrl: str, ReceiptHandle: str) -> None:  # noqa: N803
        del self.messages[ReceiptHandle]
        self.deleted.append(ReceiptHandle)


class FailingEmbedder:
    """Embedding provider whose every call fails (simulates a Bedrock outage)."""

    dimension = 8

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Raise unconditionally."""
        raise RuntimeError("bedrock down")
