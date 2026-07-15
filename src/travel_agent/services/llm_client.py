"""LLM Provider abstraction layer.

Supports multiple LLM providers through a unified get_llm() interface.
All providers return a LangChain BaseChatModel so Agent code never
needs to know which provider is active.

Supported providers (controlled via LLM_PROVIDER in .env):
  - openai   → ChatOpenAI (gpt-4o-mini default)
  - deepseek → ChatOpenAI with DeepSeek API (deepseek-chat default)
  - glm      → ChatOpenAI with Zhipu GLM API (glm-4 default)
"""

import os
from enum import Enum
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from travel_agent.config import settings


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GLM = "glm"


# ── Provider configuration ──

_PROVIDER_CONFIG: dict[ProviderType, dict] = {
    ProviderType.OPENAI: {
        "default_model": "gpt-4o-mini",
        "base_url": None,
    },
    ProviderType.DEEPSEEK: {
        "default_model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
    },
    ProviderType.GLM: {
        "default_model": "glm-4",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
}


# ── Public API ──


def get_llm() -> BaseChatModel:
    """Get a configured chat model for the active LLM provider.

    Provider is selected via the ``LLM_PROVIDER`` environment variable.
    API key and model are read from the corresponding environment vars.

    Returns:
        A configured LangChain BaseChatModel ready for invoke() /
        with_structured_output().

    Raises:
        ValueError: If the provider is unknown or its API key is missing.
    """
    provider_name = (settings.LLM_PROVIDER or "openai").strip().lower()

    try:
        provider = ProviderType(provider_name)
    except ValueError:
        raise ValueError(
            f"Unsupported LLM provider: '{provider_name}'. "
            f"Options: {', '.join(p.value for p in ProviderType)}"
        )

    api_key = _resolve_api_key(provider)
    model = _resolve_model(provider)
    base_url = _PROVIDER_CONFIG[provider]["base_url"]

    kwargs: dict = {
        "model": model,
        "temperature": 0,
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)


def get_provider_info() -> dict:
    """Return info about the currently active provider.

    Useful for the frontend to display which LLM is being used.
    """
    provider = (settings.LLM_PROVIDER or "openai").strip().lower()
    model = _resolve_model_for_name(provider)
    return {
        "provider": provider,
        "model": model,
    }


# ── Internal helpers ──


def _resolve_api_key(provider: ProviderType) -> str:
    """Get the API key for the given provider from settings or env."""
    mapping = {
        ProviderType.OPENAI: (
            "OPENAI_API_KEY",
            settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY") or "",
        ),
        ProviderType.DEEPSEEK: (
            "DEEPSEEK_API_KEY",
            settings.DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY") or "",
        ),
        ProviderType.GLM: (
            "GLM_API_KEY",
            settings.GLM_API_KEY or os.getenv("GLM_API_KEY") or "",
        ),
    }
    env_name, key = mapping[provider]
    if not key:
        raise ValueError(
            f"{env_name} is not set. "
            f"Add it to your .env file for the {provider.value} provider."
        )
    return key


def _resolve_model(provider: ProviderType) -> str:
    """Get the model name for the given provider."""
    model = _resolve_model_for_name(provider.value)
    if model:
        return model
    return _PROVIDER_CONFIG[provider]["default_model"]


def _resolve_model_for_name(provider_name: str) -> Optional[str]:
    """Resolve model name from settings by provider name string."""
    mapping = {
        "openai": settings.OPENAI_MODEL_NAME,
        "deepseek": settings.DEEPSEEK_MODEL_NAME,
        "glm": settings.GLM_MODEL_NAME,
    }
    return mapping.get(provider_name)
