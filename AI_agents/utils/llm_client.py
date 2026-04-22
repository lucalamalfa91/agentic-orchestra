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
    logger.info(f"[llm_client] get_llm_client called with provider='{provider}', config={config}")

    if config is None:
        config = {}

    provider = provider.lower()
    logger.info(f"[llm_client] Normalized provider: '{provider}'")

    # Default configuration
    temperature = config.get("temperature", 0.1)  # Low temp for deterministic design
    max_tokens = config.get("max_tokens", 4000)
    logger.info(f"[llm_client] Config: temperature={temperature}, max_tokens={max_tokens}")

    if provider == "openai":
        logger.info("[llm_client] Provider is 'openai', attempting to create ChatOpenAI client")
        try:
            from langchain_openai import ChatOpenAI
            logger.info("[llm_client] Successfully imported ChatOpenAI")
        except ImportError as e:
            logger.error(f"[llm_client] Failed to import ChatOpenAI: {e}")
            raise ImportError(
                "langchain-openai not installed. "
                "Run: pip install langchain-openai"
            )

        # Support OpenAI and OpenAI-compatible providers (ADESSO AI Hub, etc.)
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ADESSO_AI_HUB_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("ADESSO_BASE_URL")

        logger.info(f"[llm_client] OPENAI_API_KEY present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
        logger.info(f"[llm_client] OPENAI_BASE_URL: {base_url if base_url else 'not set (using default)'}")

        if not api_key:
            logger.error("[llm_client] No OPENAI_API_KEY or ADESSO_AI_HUB_KEY found in environment")
            raise ValueError(
                "OPENAI_API_KEY or ADESSO_AI_HUB_KEY environment variable not set. "
                "Backend must inject user's API key before agent execution."
            )

        # Use appropriate default model based on provider
        # Priority: config dict > OPENAI_MODEL env var > default
        env_model = os.getenv("OPENAI_MODEL")
        if base_url and "adesso" in base_url.lower():
            model = config.get("model") or env_model or "gpt-4o-mini"
            logger.info(f"[llm_client] Creating ADESSO AI Hub client: {model}")
        else:
            model = config.get("model") or env_model or "gpt-4o"
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

        logger.info(f"[llm_client] Creating ChatOpenAI with kwargs: model={model}, base_url={base_url}, temperature={temperature}, max_tokens={max_tokens}")
        try:
            client = ChatOpenAI(**kwargs)
            logger.info(f"[llm_client] ✓ Successfully created ChatOpenAI client")
            return client
        except Exception as e:
            logger.error(f"[llm_client] ✗ Failed to create ChatOpenAI client: {type(e).__name__}: {e}")
            raise

    elif provider == "anthropic":
        logger.info("[llm_client] Provider is 'anthropic', attempting to create ChatAnthropic client")
        try:
            from langchain_anthropic import ChatAnthropic
            logger.info("[llm_client] Successfully imported ChatAnthropic")
        except ImportError as e:
            logger.error(f"[llm_client] Failed to import ChatAnthropic: {e}")
            raise ImportError(
                "langchain-anthropic not installed. "
                "Run: pip install langchain-anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        logger.info(f"[llm_client] ANTHROPIC_API_KEY present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")

        if not api_key:
            logger.error("[llm_client] No ANTHROPIC_API_KEY found in environment")
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Backend must inject user's API key before agent execution."
            )

        # Support custom Anthropic-compatible endpoints
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        logger.info(f"[llm_client] ANTHROPIC_BASE_URL: {base_url if base_url else 'not set (using official API)'}")

        # Get model from config or env var, with fallback chain
        model = config.get("model") or os.getenv("ANTHROPIC_MODEL")
        if not model:
            model = "claude-sonnet-4-6"

        logger.info(f"[llm_client] Creating Anthropic client: {model}")

        # Enforce per-model output token limits for older models that cap at 4096.
        # Newer models (claude-sonnet-4-6, claude-3-5-*) support 8K–64K and are uncapped.
        _ANTHROPIC_MAX_OUTPUT = {
            "claude-3-haiku-20240307": 4096,
            "claude-3-opus-20240229": 4096,
        }
        model_limit = _ANTHROPIC_MAX_OUTPUT.get(model)
        if model_limit and max_tokens > model_limit:
            logger.warning(
                f"[llm_client] max_tokens={max_tokens} exceeds limit for {model} "
                f"({model_limit}), capping to {model_limit}"
            )
            max_tokens = model_limit

        # Create client with optional base_url
        kwargs = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url
            logger.info(f"[llm_client] Using custom Anthropic endpoint: {base_url}")

        logger.info(f"[llm_client] Creating ChatAnthropic with kwargs: model={model}, base_url={base_url}, temperature={temperature}, max_tokens={max_tokens}")
        try:
            client = ChatAnthropic(**kwargs)
            logger.info(f"[llm_client] ✓ Successfully created ChatAnthropic client")
            return client
        except Exception as e:
            logger.error(f"[llm_client] ✗ Failed to create ChatAnthropic client: {type(e).__name__}: {e}")
            raise

    else:
        logger.error(f"[llm_client] Unsupported provider: '{provider}'")
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: openai, anthropic"
        )
