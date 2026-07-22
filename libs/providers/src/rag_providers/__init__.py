"""LLM provider protocols, deterministic fakes, and Bedrock implementations.

See ADR-0006: local/unit code always runs against fakes; real Bedrock calls
happen only where AWS credentials and region configuration are available
(llm-smoke workflow).
"""

__version__ = "0.1.0"
