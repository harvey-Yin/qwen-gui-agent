"""
Ollama LLM Client for GUI-Agent
Handles communication with Ollama API for vision-language model inference.
"""
import base64
import json
import requests
from typing import Optional, List, Dict, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(
        self,
        base_url: str = config.OLLAMA_BASE_URL,
        model: str = config.OLLAMA_MODEL
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.generate_endpoint = f"{self.base_url}/api/generate"
    
    def test_connection(self) -> bool:
        """Test if Ollama server is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except requests.RequestException:
            return []
    
    def encode_image(self, image_path: str) -> str:
        """Encode image file to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def encode_image_bytes(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64."""
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        images: Optional[List[str]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat request to Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            images: List of base64 encoded images
            stream: Whether to stream the response
            
        Returns:
            Response dict with 'message' containing assistant reply
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        # Add images to the last user message if provided
        if images and messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    msg["images"] = images
                    break
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def chat_with_image(
        self,
        user_message: str,
        image_base64: str,
        system_prompt: str = config.SYSTEM_PROMPT,
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
        messages = []
        
        # Add system message
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add history
        if history:
            messages.extend(history)
        
        # Add current user message with image
        messages.append({
            "role": "user",
            "content": user_message,
            "images": [image_base64]
        })
        
        result = self.chat(messages)
        
        if "error" in result:
            return json.dumps({
                "thought": f"Error communicating with LLM: {result['error']}",
                "action": {"type": "done", "params": {"message": "LLM error"}},
                "status": "failed"
            })
        
        # Handle different response formats
        message = result.get("message", {})
        if isinstance(message, str):
            return message
        elif isinstance(message, dict):
            return message.get("content", "")
        else:
            return ""
    
    def parse_action_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the JSON action response from LLM.
        
        Args:
            response: Raw response string from LLM
            
        Returns:
            Parsed action dict or error dict
        """
        # Try to extract JSON from the response
        response = response.strip()
        
        # Handle /think and /no_think tags from qwen3
        if "/think" in response or "/no_think" in response:
            # Remove thinking tags and their content
            import re
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            response = response.strip()
        
        # Find JSON in the response
        try:
            # Try direct parse first
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON block
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return error if no valid JSON found
        return {
            "thought": f"Failed to parse LLM response: {response[:200]}",
            "action": {"type": "done", "params": {"message": "Parse error"}},
            "status": "failed"
        }


if __name__ == "__main__":
    # Test the client
    client = OllamaClient()
    print(f"Connection test: {client.test_connection()}")
    print(f"Available models: {client.get_available_models()}")
