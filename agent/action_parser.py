"""
Action Parser for GUI-Agent
Parses and validates LLM action responses.
"""
import json
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from enum import Enum


class ActionType(str, Enum):
    CLICK = "click"
    MOVE = "move"
    TYPE = "type"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    DONE = "done"


class ClickParams(BaseModel):
    x: int
    y: int
    button: str = "left"
    clicks: int = 1


class MoveParams(BaseModel):
    x: int
    y: int


class TypeParams(BaseModel):
    text: str
    interval: float = 0.02


class HotkeyParams(BaseModel):
    keys: list[str]


class ScrollParams(BaseModel):
    amount: int
    x: Optional[int] = None
    y: Optional[int] = None


class WaitParams(BaseModel):
    seconds: float = 1.0


class DoneParams(BaseModel):
    message: str = "Task completed"


class ScreenshotParams(BaseModel):
    region: Optional[list[int]] = None


class AgentAction(BaseModel):
    """Validated agent action."""
    type: ActionType
    params: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Full agent response structure."""
    thought: str
    action: AgentAction
    status: str = "in_progress"  # in_progress, completed, failed


class ActionParser:
    """Parser for LLM action responses."""
    
    PARAM_VALIDATORS = {
        ActionType.CLICK: ClickParams,
        ActionType.MOVE: MoveParams,
        ActionType.TYPE: TypeParams,
        ActionType.HOTKEY: HotkeyParams,
        ActionType.SCROLL: ScrollParams,
        ActionType.WAIT: WaitParams,
        ActionType.DONE: DoneParams,
        ActionType.SCREENSHOT: ScreenshotParams,
    }
    
    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        """Extract JSON from text that may contain other content."""
        # Remove thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Remove /no_think or /think markers
        text = re.sub(r'/no_think|/think', '', text)
        text = text.strip()
        
        # Remove common prefixes like "步骤1:" or "Step 1:"
        text = re.sub(r'^(步骤|Step)\s*\d+\s*[:：]\s*', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Try to find JSON block
        # Look for code block first
        code_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if code_match:
            return code_match.group(1)
        
        # Look for raw JSON - find the first complete JSON object
        # Use a more robust pattern that handles nested braces
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    return text[start_idx:i+1]
        
        return None
    
    def parse(self, response: str) -> AgentResponse:
        """
        Parse LLM response into AgentResponse.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            AgentResponse object
        """
        # Extract JSON
        json_str = self.extract_json(response)
        
        if not json_str:
            return AgentResponse(
                thought=f"Failed to find JSON in response: {response[:200]}",
                action=AgentAction(
                    type=ActionType.DONE,
                    params={"message": "Parse error: No JSON found"}
                ),
                status="failed"
            )
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return AgentResponse(
                thought=f"Failed to parse JSON: {e}",
                action=AgentAction(
                    type=ActionType.DONE,
                    params={"message": f"JSON parse error: {e}"}
                ),
                status="failed"
            )
        
        # Validate structure
        try:
            # Ensure data is a dict
            if not isinstance(data, dict):
                return AgentResponse(
                    thought=f"Response is not a dict: {type(data)}",
                    action=AgentAction(
                        type=ActionType.DONE,
                        params={"message": "Invalid response format"}
                    ),
                    status="failed"
                )
            
            # Extract components
            thought = data.get("thought", "No thought provided")
            status = data.get("status", "in_progress")
            
            action_data = data.get("action", {})
            
            # Handle case where action is a string or None
            if not isinstance(action_data, dict):
                return AgentResponse(
                    thought=thought,
                    action=AgentAction(
                        type=ActionType.DONE,
                        params={"message": f"Invalid action format: {type(action_data)}"}
                    ),
                    status="failed"
                )
            
            action_type_str = action_data.get("type", "done")
            action_params = action_data.get("params", {})
            
            # Validate action type
            try:
                action_type = ActionType(action_type_str)
            except ValueError:
                return AgentResponse(
                    thought=thought,
                    action=AgentAction(
                        type=ActionType.DONE,
                        params={"message": f"Unknown action type: {action_type_str}"}
                    ),
                    status="failed"
                )
            
            # Validate params
            validator = self.PARAM_VALIDATORS.get(action_type)
            if validator:
                try:
                    validated_params = validator(**action_params)
                    action_params = validated_params.model_dump()
                except ValidationError as e:
                    return AgentResponse(
                        thought=thought,
                        action=AgentAction(
                            type=ActionType.DONE,
                            params={"message": f"Invalid params: {e}"}
                        ),
                        status="failed"
                    )
            
            return AgentResponse(
                thought=thought,
                action=AgentAction(type=action_type, params=action_params),
                status=status
            )
            
        except Exception as e:
            return AgentResponse(
                thought=f"Validation error: {e}",
                action=AgentAction(
                    type=ActionType.DONE,
                    params={"message": str(e)}
                ),
                status="failed"
            )
    
    def to_dict(self, response: AgentResponse) -> Dict[str, Any]:
        """Convert AgentResponse to dictionary."""
        return {
            "thought": response.thought,
            "action": {
                "type": response.action.type.value,
                "params": response.action.params
            },
            "status": response.status
        }


if __name__ == "__main__":
    # Test parser
    parser = ActionParser()
    
    test_response = '''
    {
        "thought": "I see the desktop, need to click start menu",
        "action": {
            "type": "click",
            "params": {"x": 50, "y": 1050}
        },
        "status": "in_progress"
    }
    '''
    
    result = parser.parse(test_response)
    print(f"Parsed: {result}")
