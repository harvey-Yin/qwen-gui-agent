"""
OpenAI-Compatible VLM Client for GUI-Agent.
Supports any OpenAI-compatible API: Qwen API, SiliconFlow, OpenRouter, etc.
"""
import json
import requests
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm.base_client import VLMClient


class OpenAICompatClient(VLMClient):
    """
    Client for OpenAI-compatible vision-language model APIs.

    Supports:
      - Qwen API (dashscope): https://dashscope.aliyuncs.com/compatible-mode/v1
      - SiliconFlow: https://api.siliconflow.cn/v1
      - OpenRouter: https://openrouter.ai/api/v1
      - Any other OpenAI-compatible endpoint
    """

    def __init__(
        self,
        base_url: str = config.OPENAI_BASE_URL,
        api_key: str = config.OPENAI_API_KEY,
        model: str = config.OPENAI_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    # ── interface implementation ──────────────────────────────────────

    def test_connection(self) -> bool:
        """Test if the API endpoint is reachable by listing models."""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers=self._headers(),
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def get_model_name(self) -> str:
        return self.model

    def chat_with_image(
        self,
        user_message: str,
        image_base64: str,
        system_prompt: str = config.SYSTEM_PROMPT,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a multimodal chat request using OpenAI vision format."""
        messages: List[Dict[str, Any]] = []

        # System prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # History – convert Ollama-style history to OpenAI style
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", ""),
                })

        # Current turn with image
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
            ],
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
        }

        try:
            resp = requests.post(
                self.chat_endpoint,
                headers=self._headers(),
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            # Extract assistant message
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

        except requests.RequestException as e:
            return json.dumps({
                "thought": f"Error communicating with API: {e}",
                "action": {"type": "done", "params": {"message": "API error"}},
                "status": "failed",
            })

    # ── helpers ───────────────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h


if __name__ == "__main__":
    client = OpenAICompatClient()
    print(f"Connection test: {client.test_connection()}")
    print(f"Model: {client.get_model_name()}")
