"""
Connecteurs LLM (Gemini, Azure OpenAI, DeepSeek) + factory.
"""

from .base import LLMClient
from .factory import get_llm

__all__ = ["LLMClient", "get_llm"]
