"""
GUI Tools for GUI-Agent
PyAutoGUI wrapper with safety features and logging.
"""
import time
from typing import Optional, Tuple, List, Dict, Any
import pyautogui

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


# Configure PyAutoGUI safety features
pyautogui.PAUSE = config.PYAUTOGUI_PAUSE
pyautogui.FAILSAFE = config.PYAUTOGUI_FAILSAFE


class GUITools:
    """Safe wrapper for PyAutoGUI operations."""
    
    def __init__(self):
        self.action_log: List[Dict[str, Any]] = []
    
    def _log_action(self, action_type: str, params: Dict[str, Any], success: bool):
        """Log an action for debugging."""
        self.action_log.append({
            "type": action_type,
            "params": params,
            "success": success,
            "timestamp": time.time()
        })
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return pyautogui.size()
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()
    
    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1
    ) -> bool:
        """
        Perform mouse click.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks (1 or 2 for double-click)
            
        Returns:
            True if successful
        """
        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            self._log_action("click", {"x": x, "y": y, "button": button, "clicks": clicks}, True)
            return True
        except Exception as e:
            self._log_action("click", {"x": x, "y": y, "error": str(e)}, False)
            return False
    
    def move(self, x: int, y: int, duration: float = 0.2) -> bool:
        """
        Move mouse to position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Animation duration
            
        Returns:
            True if successful
        """
        try:
            pyautogui.moveTo(x=x, y=y, duration=duration)
            self._log_action("move", {"x": x, "y": y}, True)
            return True
        except Exception as e:
            self._log_action("move", {"x": x, "y": y, "error": str(e)}, False)
            return False
    
    def type_text(self, text: str, interval: float = 0.02) -> bool:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
            
        Returns:
            True if successful
        """
        try:
            # Use pyperclip and paste for Chinese support
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            self._log_action("type", {"text": text}, True)
            return True
        except ImportError:
            # Fallback to direct typing (ASCII only)
            try:
                pyautogui.typewrite(text, interval=interval)
                self._log_action("type", {"text": text}, True)
                return True
            except Exception as e:
                self._log_action("type", {"text": text, "error": str(e)}, False)
                return False
        except Exception as e:
            self._log_action("type", {"text": text, "error": str(e)}, False)
            return False
    
    def hotkey(self, keys: List[str]) -> bool:
        """
        Press a keyboard shortcut.
        
        Args:
            keys: List of keys to press together, e.g., ['ctrl', 'c']
            
        Returns:
            True if successful
        """
        try:
            pyautogui.hotkey(*keys)
            self._log_action("hotkey", {"keys": keys}, True)
            return True
        except Exception as e:
            self._log_action("hotkey", {"keys": keys, "error": str(e)}, False)
            return False
    
    def scroll(
        self,
        amount: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> bool:
        """
        Scroll the mouse wheel.
        
        Args:
            amount: Positive for up, negative for down
            x: Optional X position
            y: Optional Y position
            
        Returns:
            True if successful
        """
        try:
            pyautogui.scroll(amount, x=x, y=y)
            self._log_action("scroll", {"amount": amount, "x": x, "y": y}, True)
            return True
        except Exception as e:
            self._log_action("scroll", {"amount": amount, "error": str(e)}, False)
            return False
    
    def wait(self, seconds: float) -> bool:
        """
        Wait for specified time.
        
        Args:
            seconds: Time to wait
            
        Returns:
            True
        """
        time.sleep(seconds)
        self._log_action("wait", {"seconds": seconds}, True)
        return True
    
    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute an action from LLM response.
        
        Args:
            action: Action dict with 'type' and 'params'
            
        Returns:
            Tuple of (success, message)
        """
        # Handle case where action is not a dict
        if not isinstance(action, dict):
            return False, f"Invalid action format: {type(action)}"
        
        action_type = action.get("type", "")
        params = action.get("params", {})
        
        # Ensure params is a dict
        if not isinstance(params, dict):
            params = {}
        
        if action_type == "click":
            x = params.get("x", 0)
            y = params.get("y", 0)
            button = params.get("button", "left")
            clicks = params.get("clicks", 1)
            success = self.click(x, y, button, clicks)
            return success, f"Clicked at ({x}, {y})"
        
        elif action_type == "move":
            x = params.get("x", 0)
            y = params.get("y", 0)
            success = self.move(x, y)
            return success, f"Moved to ({x}, {y})"
        
        elif action_type == "type":
            text = params.get("text", "")
            success = self.type_text(text)
            return success, f"Typed: {text[:50]}..."
        
        elif action_type == "hotkey":
            keys = params.get("keys", [])
            success = self.hotkey(keys)
            return success, f"Pressed: {'+'.join(keys)}"
        
        elif action_type == "scroll":
            amount = params.get("amount", 0)
            x = params.get("x")
            y = params.get("y")
            success = self.scroll(amount, x, y)
            return success, f"Scrolled {amount}"
        
        elif action_type == "wait":
            seconds = params.get("seconds", 1)
            success = self.wait(seconds)
            return success, f"Waited {seconds}s"
        
        elif action_type == "done":
            message = params.get("message", "Task completed")
            return True, message
        
        elif action_type == "screenshot":
            # Screenshot is handled by the orchestrator
            return True, "Screenshot requested"
        
        else:
            return False, f"Unknown action type: {action_type}"
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Get the action log."""
        return self.action_log.copy()
    
    def clear_action_log(self):
        """Clear the action log."""
        self.action_log.clear()


if __name__ == "__main__":
    # Test GUI tools
    tools = GUITools()
    print(f"Screen size: {tools.get_screen_size()}")
    print(f"Mouse position: {tools.get_mouse_position()}")
