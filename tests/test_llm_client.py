"""Tests for LLM Provider abstraction layer.

Validates:
1. Provider factory creates correct model types
2. Provider switching via env var
3. Missing API key raises helpful error
4. Unknown provider raises helpful error
"""

import os
from unittest.mock import patch

import pytest

from travel_agent.config import settings
from travel_agent.services.llm_client import (
    ProviderType,
    get_llm,
    get_provider_info,
    _resolve_api_key,
    _resolve_model,
)


class TestProviderBasics:
    """Basic provider configuration and info."""

    def test_default_provider_is_openai(self):
        """Default provider should be openai with gpt-4o-mini."""
        info = get_provider_info()
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4o-mini"

    def test_provider_type_enum(self):
        """ProviderType enum should have all expected values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.DEEPSEEK.value == "deepseek"
        assert ProviderType.GLM.value == "glm"

    def test_model_resolution_per_provider(self):
        """_resolve_model should return correct defaults."""
        assert "gpt-4o-mini" in _resolve_model(ProviderType.OPENAI)
        assert "deepseek" in _resolve_model(ProviderType.DEEPSEEK).lower()
        assert "glm" in _resolve_model(ProviderType.GLM).lower()


class TestProviderSwitching:
    """Runtime provider switching via environment."""

    def setup_method(self):
        """Store original env values before each test."""
        self._orig_provider = os.environ.get("LLM_PROVIDER")
        self._orig_openai_key = os.environ.get("OPENAI_API_KEY")
        self._orig_deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        self._orig_glm_key = os.environ.get("GLM_API_KEY")

    def teardown_method(self):
        """Restore original env values after each test."""
        for key, val in [
            ("LLM_PROVIDER", self._orig_provider),
            ("OPENAI_API_KEY", self._orig_openai_key),
            ("DEEPSEEK_API_KEY", self._orig_deepseek_key),
            ("GLM_API_KEY", self._orig_glm_key),
        ]:
            if val is not None:
                os.environ[key] = val
            elif key in os.environ:
                del os.environ[key]
        settings.LLM_PROVIDER = self._orig_provider or "openai"

    @patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"})
    def test_switch_to_openai(self):
        """Switching to openai should create an OpenAI model."""
        settings.LLM_PROVIDER = "openai"
        llm = get_llm()
        assert llm is not None
        assert llm.model == "gpt-4o-mini"
        info = get_provider_info()
        assert info["provider"] == "openai"

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "deepseek",
        "DEEPSEEK_API_KEY": "sk-test-deepseek",
    })
    def test_switch_to_deepseek(self):
        """Switching to deepseek should configure DeepSeek base_url."""
        settings.LLM_PROVIDER = "deepseek"
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-deepseek"
        llm = get_llm()
        assert llm is not None
        assert "deepseek" in llm.model
        info = get_provider_info()
        assert info["provider"] == "deepseek"

    @patch.dict(os.environ, {
        "LLM_PROVIDER": "glm",
        "GLM_API_KEY": "sk-test-glm",
    })
    def test_switch_to_glm(self):
        """Switching to glm should configure GLM base_url."""
        settings.LLM_PROVIDER = "glm"
        llm = get_llm()
        assert llm is not None
        assert "glm" in llm.model
        info = get_provider_info()
        assert info["provider"] == "glm"

    @patch.dict(os.environ, {"LLM_PROVIDER": "nonexistent"})
    def test_unknown_provider_raises_error(self):
        """Unknown provider should raise ValueError with options."""
        settings.LLM_PROVIDER = "nonexistent"
        with pytest.raises(ValueError) as exc:
            get_llm()
        assert "openai" in str(exc.value)
        assert "deepseek" in str(exc.value)
        assert "glm" in str(exc.value)


class TestApiKeyValidation:
    """API key missing / validation."""

    def test_missing_openai_key(self):
        """Missing OPENAI_API_KEY should raise ValueError."""
        settings.LLM_PROVIDER = "openai"
        # Ensure no key is set
        with patch.dict(os.environ, {}, clear=True):
            settings.OPENAI_API_KEY = ""
            with pytest.raises(ValueError) as exc:
                get_llm()
            assert "OPENAI_API_KEY" in str(exc.value)

    def test_missing_deepseek_key(self):
        """Missing DEEPSEEK_API_KEY should raise ValueError."""
        settings.LLM_PROVIDER = "deepseek"
        with patch.dict(os.environ, {}, clear=True):
            settings.DEEPSEEK_API_KEY = ""
            with pytest.raises(ValueError) as exc:
                get_llm()
            assert "DEEPSEEK_API_KEY" in str(exc.value)

    def test_missing_glm_key(self):
        """Missing GLM_API_KEY should raise ValueError."""
        settings.LLM_PROVIDER = "glm"
        with patch.dict(os.environ, {}, clear=True):
            settings.GLM_API_KEY = ""
            with pytest.raises(ValueError) as exc:
                get_llm()
            assert "GLM_API_KEY" in str(exc.value)

    def test_api_key_from_environment(self):
        """API key should be readable from os.environ fallback."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-env-key",
        }):
            settings.LLM_PROVIDER = "openai"
            settings.OPENAI_API_KEY = ""
            llm = get_llm()
            assert llm is not None


class TestCoordinatorFallback:
    """Coordinator still falls back to regex parser when no LLM."""

    def test_fallback_still_works(self):
        """Without API key, coordinator should use fallback parser."""
        from travel_agent.agents.coordinator import coordinator_node
        from travel_agent.graph.state import create_initial_state

        state = create_initial_state("去北京玩3天，预算3000")
        result = coordinator_node(state)

        assert "travel_intent" in result
        intent = result["travel_intent"]
        assert intent is not None
        assert "北京" in (intent.destination or "")
