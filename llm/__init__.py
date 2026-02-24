"""
LLM Client Package.
Provides a factory function to create the appropriate VLM client
based on the configured provider.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm.base_client import VLMClient


def create_client(provider: str = config.LLM_PROVIDER, **kwargs) -> VLMClient:
    """
    Factory function to create a VLM client.

    Args:
        provider: "ollama" or "openai_compat"
        **kwargs: Override default config values (base_url, api_key, model, etc.)

    Returns:
        A VLMClient instance
    """
    if provider == "ollama":
        from llm.ollama_client import OllamaClient
        return OllamaClient(
            base_url=kwargs.get("base_url", config.OLLAMA_BASE_URL),
            model=kwargs.get("model", config.OLLAMA_MODEL),
        )
    elif provider == "openai_compat":
        from llm.openai_compat_client import OpenAICompatClient
        return OpenAICompatClient(
            base_url=kwargs.get("base_url", config.OPENAI_BASE_URL),
            api_key=kwargs.get("api_key", config.OPENAI_API_KEY),
            model=kwargs.get("model", config.OPENAI_MODEL),
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'ollama' or 'openai_compat'.")
