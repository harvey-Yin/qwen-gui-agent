"""
Local GLM VLM Client for GUI-Agent.
Uses ModelScope/Transformers to run GLM-4.6V-Flash locally on GPU.

Requirements:
  pip install modelscope torch torchvision transformers accelerate
"""
import json
import base64
import logging
from io import BytesIO
from typing import Optional, List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm.base_client import VLMClient

logger = logging.getLogger(__name__)


class GLMLocalClient(VLMClient):
    """
    Client for locally deployed GLM-4.6V-Flash using Transformers.

    The model is loaded lazily on first call to chat_with_image()
    to avoid slow startup when just constructing the client.

    GPU memory: ~7GB with float16, ~14GB with float32.
    """

    def __init__(
        self,
        model_path: str = config.GLM_LOCAL_MODEL_PATH,
        device_map: str = config.GLM_LOCAL_DEVICE,
        torch_dtype: str = config.GLM_LOCAL_DTYPE,
    ):
        self.model_path = model_path
        self.device_map = device_map
        self.torch_dtype_str = torch_dtype

        # Lazy-loaded
        self._model = None
        self._processor = None
        self._loaded = False

    def _load_model(self):
        """Load model and processor on first use (4-bit quantized)."""
        if self._loaded:
            return

        logger.info(f"[GLM-Local] Loading model: {self.model_path} ...")
        logger.info(f"[GLM-Local] device_map={self.device_map}, using 4-bit NF4 quantization")

        import torch
        from modelscope import AutoProcessor, Glm4vForConditionalGeneration
        from transformers import BitsAndBytesConfig

        # 4-bit quantization: ~14GB float16 → ~4GB NF4
        # This ensures the model fits entirely in 12GB VRAM
        # with room for KV cache and activations.
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        self._processor = AutoProcessor.from_pretrained(self.model_path)
        self._model = Glm4vForConditionalGeneration.from_pretrained(
            pretrained_model_name_or_path=self.model_path,
            quantization_config=quantization_config,
            device_map=self.device_map,
        )
        self._loaded = True
        logger.info(f"[GLM-Local] Model loaded (4-bit) on {self._model.device}")

    # ── interface implementation ──────────────────────────────────────

    def test_connection(self) -> bool:
        """Check if model can be loaded (or is already loaded)."""
        try:
            import torch
            if not torch.cuda.is_available() and self.device_map != "cpu":
                logger.warning("[GLM-Local] CUDA not available")
                return False
            # Don't actually load the full model just for a test
            if self._loaded:
                return True
            # Check that the libraries are importable
            from modelscope import AutoProcessor, Glm4vForConditionalGeneration
            return True
        except ImportError as e:
            logger.error(f"[GLM-Local] Missing dependency: {e}")
            return False

    def get_model_name(self) -> str:
        return self.model_path

    def chat_with_image(
        self,
        user_message: str,
        image_base64: str,
        system_prompt: str = config.SYSTEM_PROMPT,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Run local inference on a screenshot.

        Args:
            user_message: Text prompt
            image_base64: Base64 encoded JPEG screenshot
            system_prompt: System instructions
            history: Conversation history (used as text context only)

        Returns:
            Model's response text
        """
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"[GLM-Local] Failed to load model: {e}")
            return json.dumps({
                "thought": f"Failed to load local GLM model: {e}",
                "action": {"type": "done", "params": {"message": "Model load error"}},
                "status": "failed",
            })

        try:
            from PIL import Image

            # Decode base64 → PIL Image
            img_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(img_bytes)).convert("RGB")

            # Build messages in GLM's native format.
            # GLM's apply_chat_template requires ALL content fields to be
            # list-of-dicts format: [{"type": "text", "text": "..."}].
            # Plain strings cause "string indices must be integers".
            messages: List[Dict[str, Any]] = []

            # Embed system prompt into the user message text
            # (GLM's chat template doesn't handle system role well)
            prompt_text = user_message
            if system_prompt:
                prompt_text = system_prompt.strip() + "\n\n" + user_message

            # Add text-only history (content must be list format)
            if history:
                for msg in history:
                    raw = msg.get("content", "")
                    # Wrap plain string content as list
                    if isinstance(raw, str):
                        content = [{"type": "text", "text": raw}]
                    else:
                        content = raw
                    messages.append({"role": msg["role"], "content": content})

            # Current turn: image + text
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt_text},
                ],
            })

            # Tokenize
            inputs = self._processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self._model.device)
            inputs.pop("token_type_ids", None)

            # Generate
            import torch
            with torch.no_grad():
                generated_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=1024,
                )

            # Decode only new tokens
            output_text = self._processor.decode(
                generated_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )
            return output_text.strip()

        except Exception as e:
            logger.error(f"[GLM-Local] Inference error: {e}")
            return json.dumps({
                "thought": f"Local GLM inference error: {e}",
                "action": {"type": "done", "params": {"message": "Inference error"}},
                "status": "failed",
            })


if __name__ == "__main__":
    client = GLMLocalClient()
    print(f"Connection test: {client.test_connection()}")
    print(f"Model: {client.get_model_name()}")
