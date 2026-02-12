"""
Abstract Base Class for VLM Clients.
All LLM providers (Ollama, OpenAI-compatible APIs) must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class VLMClient(ABC):
    """Abstract base class for Vision-Language Model clients."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the LLM service is accessible."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the current model."""
        ...

    @abstractmethod
    def chat_with_image(
        self,
        user_message: str,
        image_base64: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Send a chat message with an image and get response.

        Args:
            user_message: The user's text message
            image_base64: Base64 encoded screenshot
            system_prompt: System prompt for the agent
            history: Previous conversation history

        Returns:
            The assistant's response text
        """
        ...
