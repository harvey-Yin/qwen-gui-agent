"""
ZhipuAI GLM Native Client for GUI-Agent.
Uses the official zai-sdk for GLM-4.6V-Flash and other GLM models.

Key differences from OpenAI-compat client:
  - Base64 images: raw base64 string (no "data:image/jpeg;base64," prefix)
  - Supports "thinking" parameter for chain-of-thought reasoning
  - Built-in retry / connection management via httpx
"""
import json
import time
import logging
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm.base_client import VLMClient

logger = logging.getLogger(__name__)


class GLMClient(VLMClient):
    """
    Client for ZhipuAI GLM models using the official zai-sdk.

    Supported models:
      - glm-4.6v-flash  (fast, free tier, multimodal)
      - glm-4v-plus     (more capable multimodal)
      - glm-4v          (standard multimodal)
    """

    def __init__(
        self,
        api_key: str = config.GLM_API_KEY,
        model: str = config.GLM_API_MODEL,
        enable_thinking: bool = False,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        try:
            from zai import ZhipuAiClient
        except ImportError:
            raise ImportError(
                "zai-sdk is not installed. Run: pip install zai-sdk"
            )

        self.client = ZhipuAiClient(api_key=api_key)
        self.model = model
        self.enable_thinking = enable_thinking
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ── interface implementation ──────────────────────────────────────

    def test_connection(self) -> bool:
        """Test API connectivity with a minimal text request."""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            return bool(resp.choices)
        except Exception as e:
            logger.warning(f"GLM connection test failed: {e}")
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
        """
        Send a multimodal chat request using the official zai-sdk.

        Note: GLM expects raw base64 in the image_url.url field
        (no "data:image/jpeg;base64," prefix).
        """
        messages: List[Dict[str, Any]] = []

        # System prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Conversation history (text only for past turns)
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", ""),
                })

        # Current turn: image + text
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        # Official SDK: raw base64, no data-URL prefix
                        "url": image_base64,
                    },
                },
                {"type": "text", "text": user_message},
            ],
        })

        # Build optional kwargs
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
        }
        if self.enable_thinking:
            kwargs["thinking"] = {"type": "enabled"}

        # Call with retry on rate-limit (429)
        wait = self.retry_delay
        last_error: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ""

                # If thinking is enabled, reasoning_content is separate;
                # we only return the final answer content for action parsing.
                return content

            except Exception as e:
                err_str = str(e)
                last_error = err_str

                # Detect rate-limit errors
                if "429" in err_str or "rate" in err_str.lower():
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"[GLM] Rate limit hit (attempt {attempt + 1}/"
                            f"{self.max_retries}), retrying in {wait:.0f}s..."
                        )
                        time.sleep(wait)
                        wait *= 2
                        continue

                # Non-retriable error or final attempt
                logger.error(f"[GLM] API error: {err_str}")
                break

        return json.dumps({
            "thought": f"Error communicating with GLM API: {last_error}",
            "action": {"type": "done", "params": {"message": "API error"}},
            "status": "failed",
        })


if __name__ == "__main__":
    client = GLMClient()
    print(f"Connection test: {client.test_connection()}")
    print(f"Model: {client.get_model_name()}")
