"""LLM provider protocols, deterministic fakes, and Gemini implementations.

See ADR-0006: local/unit code always runs against fakes; real Gemini calls
happen only where ``GEMINI_API_KEY`` is available (llm-smoke workflow).
"""

__version__ = "0.1.0"
