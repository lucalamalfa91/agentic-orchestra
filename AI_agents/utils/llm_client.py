"""
LLM Client Factory for Agentic Orchestra.

Provides a unified interface for creating LLM clients (OpenAI, Anthropic)
with configuration injected from orchestration state.

Design:
- Backend decrypts user's API keys from DB and injects them as env vars
- This factory reads env vars and returns configured LLM instances
- Never hardcode API keys or instantiate LLMs directly in agent nodes
- Always use get_llm_client() to ensure consistent configuration
"""

import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_llm_client(provider: str, config: Dict[str, Any] = None):
    """
    Factory function to create LLM client instances.

    Args:
        provider: LLM provider name ("openai" | "anthropic")
        config: Optional configuration dict with keys:
            - model: Model name override (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
            - temperature: Temperature override (default: 0.1 for design tasks)
            - max_tokens: Max tokens override

    Returns:
        Configured LLM client instance (ChatOpenAI or ChatAnthropic)

    Raises:
        ValueError: If provider is unsupported or API key is missing

    Environment Variables:
        - OPENAI_API_KEY: Required for provider="openai"
        - ANTHROPIC_API_KEY: Required for provider="anthropic"

    Examples:
        >>> llm = get_llm_client("anthropic")
        >>> llm = get_llm_client("openai", {"model": "gpt-4", "temperature": 0.3})
    """
    if config is None:
        config = {}

    provider = provider.lower()

    # Default configuration
    temperature = config.get("temperature", 0.1)  # Low temp for deterministic design
    max_tokens = config.get("max_tokens", 4000)

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. "
                "Run: pip install langchain-openai"
            )

        # Support ADESSO AI Hub (OpenAI-compatible provider)
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ADESSO_AI_HUB_KEY")
        base_url = os.getenv("ADESSO_BASE_URL")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY or ADESSO_AI_HUB_KEY environment variable not set. "
                "Backend must inject user's API key before agent execution."
            )

        # Use appropriate default model based on provider
        if base_url and "adesso" in base_url.lower():
            # ADESSO AI Hub uses different model names
            model = config.get("model", "gpt-4o-mini")  # ADESSO default
            logger.info(f"[llm_client] Creating ADESSO AI Hub client: {model}")
        else:
            model = config.get("model", "gpt-4")
            logger.info(f"[llm_client] Creating OpenAI client: {model}")

        # Create client with optional base_url
        kwargs = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. "
                "Run: pip install langchain-anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Backend must inject user's API key before agent execution."
            )

        model = config.get("model", "claude-3-5-sonnet-20241022")
        logger.info(f"[llm_client] Creating Anthropic client: {model}")

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: openai, anthropic"
        )
