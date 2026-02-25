"""
OpenAI-Compatible VLM Client for GUI-Agent.
Used for Alibaba Qwen API (DashScope) and other OpenAI-compatible endpoints.
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
        base_url: str = config.QWEN_API_BASE_URL,
        api_key: str = config.QWEN_API_KEY,
        model: str = config.QWEN_API_MODEL,
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

        max_api_retries = 3
        wait_seconds = 2
        last_error = None

        for attempt in range(max_api_retries):
            try:
                resp = requests.post(
                    self.chat_endpoint,
                    headers=self._headers(),
                    json=payload,
                    timeout=120,
                )

                # Handle 429 Rate Limit with exponential backoff
                if resp.status_code == 429:
                    import time
                    retry_after = int(resp.headers.get("Retry-After", wait_seconds))
                    sleep_time = max(retry_after, wait_seconds)
                    if attempt < max_api_retries - 1:
                        time.sleep(sleep_time)
                        wait_seconds *= 2
                        continue
                    else:
                        last_error = f"429 Rate Limit exceeded after {max_api_retries} retries"
                        break

                resp.raise_for_status()
                data = resp.json()

                # Extract assistant message
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""

            except requests.RequestException as e:
                last_error = str(e)
                break

        return json.dumps({
            "thought": f"Error communicating with API: {last_error}",
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
