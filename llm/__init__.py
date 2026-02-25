"""
LLM Client Package.
Provides a factory function to create the appropriate VLM client
based on the configured provider.

Supported providers:
  - "ollama"    : Local Ollama service (Qwen3-VL)
  - "qwen_api"  : Alibaba DashScope API (qwen3-vl-flash)
  - "glm_api"   : ZhipuAI official SDK (glm-4.6v-flash)
  - "glm_local" : Local Transformers (GLM-4.6V-Flash on GPU)
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
        provider: "ollama" | "qwen_api" | "glm_api" | "glm_local"
        **kwargs: Override default config values

    Returns:
        A VLMClient instance
    """
    if provider == "ollama":
        from llm.ollama_client import OllamaClient
        return OllamaClient(
            base_url=kwargs.get("base_url", config.OLLAMA_BASE_URL),
            model=kwargs.get("model", config.OLLAMA_MODEL),
        )

    elif provider == "qwen_api":
        from llm.openai_compat_client import OpenAICompatClient
        return OpenAICompatClient(
            base_url=kwargs.get("base_url", config.QWEN_API_BASE_URL),
            api_key=kwargs.get("api_key", config.QWEN_API_KEY),
            model=kwargs.get("model", config.QWEN_API_MODEL),
        )

    elif provider == "glm_api":
        from llm.glm_client import GLMClient
        return GLMClient(
            api_key=kwargs.get("api_key", config.GLM_API_KEY),
            model=kwargs.get("model", config.GLM_API_MODEL),
            enable_thinking=kwargs.get("enable_thinking", False),
        )

    elif provider == "glm_local":
        from llm.glm_local_client import GLMLocalClient
        return GLMLocalClient(
            model_path=kwargs.get("model_path", config.GLM_LOCAL_MODEL_PATH),
            device_map=kwargs.get("device_map", config.GLM_LOCAL_DEVICE),
            torch_dtype=kwargs.get("torch_dtype", config.GLM_LOCAL_DTYPE),
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Use 'ollama', 'qwen_api', 'glm_api', or 'glm_local'."
        )
