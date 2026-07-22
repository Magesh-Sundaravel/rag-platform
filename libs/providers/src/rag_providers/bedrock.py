"""Amazon Bedrock provider implementations via the boto3 Bedrock Runtime client."""

import asyncio
import json
from collections.abc import Sequence
from typing import Any

import boto3

from rag_providers.embedding import DEFAULT_DIMENSION
from rag_providers.generation import GenerationResult

EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
GENERATION_MODEL = "amazon.nova-micro-v1:0"


class BedrockEmbeddingProvider:
    """Embeddings from Titan Text Embeddings V2."""

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        dimension: int = DEFAULT_DIMENSION,
        client: Any | None = None,
        normalize: bool = True,
    ) -> None:
        """Configure the provider.

        Args:
            model: Bedrock embedding model ID.
            dimension: Output dimensionality requested from the model.
            client: Optional pre-built Bedrock Runtime client.
            normalize: Whether Bedrock should return normalized vectors.
        """
        self.model = model
        self.dimension = dimension
        self.normalize = normalize
        self._client = client or boto3.client("bedrock-runtime")

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts via Bedrock."""
        return await asyncio.gather(*(self._embed_one(text) for text in texts))

    async def _embed_one(self, text: str) -> list[float]:
        payload = {
            "inputText": text,
            "dimensions": self.dimension,
            "normalize": self.normalize,
        }
        response = await asyncio.to_thread(
            self._client.invoke_model,
            modelId=self.model,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )
        body = json.loads(response["body"].read())
        embedding = body.get("embedding")
        if not embedding:
            raise RuntimeError("Bedrock returned no embedding")
        return [float(value) for value in embedding]


class BedrockGenerationProvider:
    """Text generation from Amazon Nova Micro via the Converse API."""

    def __init__(
        self,
        model: str = GENERATION_MODEL,
        client: Any | None = None,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> None:
        """Configure the provider.

        Args:
            model: Bedrock generation model ID.
            client: Optional pre-built Bedrock Runtime client.
            max_tokens: Max output tokens for the response.
            temperature: Sampling temperature.
            top_p: Nucleus sampling cutoff.
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self._client = client or boto3.client("bedrock-runtime")

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate an answer via Bedrock."""
        response = await asyncio.to_thread(
            self._client.converse,
            modelId=self.model,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
                "topP": self.top_p,
            },
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(block.get("text", "") for block in content if "text" in block)
        usage = response.get("usage", {})
        return GenerationResult(
            text=text,
            prompt_tokens=int(usage.get("inputTokens", 0)),
            completion_tokens=int(usage.get("outputTokens", 0)),
        )
