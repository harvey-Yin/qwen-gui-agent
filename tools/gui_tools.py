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
        self._dpi_scale: Optional[float] = None

    def _get_dpi_scale(self) -> float:
        """
        Detect Windows DPI scale factor.
        Returns 1.0 for 100%, 1.25 for 125%, 1.5 for 150%, etc.
        """
        if self._dpi_scale is not None:
            return self._dpi_scale
        try:
            import ctypes
            # Make this process DPI-aware so we get real physical resolution
            ctypes.windll.user32.SetProcessDPIAware()
            physical_w = ctypes.windll.user32.GetSystemMetrics(0)
            logical_w = pyautogui.size()[0]
            self._dpi_scale = physical_w / logical_w if logical_w > 0 else 1.0
        except Exception:
            self._dpi_scale = 1.0
        return self._dpi_scale

    def convert_coordinates(
        self, x: int, y: int,
        image_size: Optional[Tuple[int, int]] = None,
        screen_size: Optional[Tuple[int, int]] = None,
        model_name: str = "",
    ) -> Tuple[int, int]:
        """
        Convert VLM output coordinates to real screen pixel coordinates.

        Supports three modes via config.COORD_FORMAT:
          - "normalized_1000": Qwen3-VL (Ollama) — coords in 0-1000 grid
          - "absolute":        Qwen API / Qwen2.5-VL — pixel coords matching image sent to LLM
          - "auto":            Auto-detect based on model name

        Also handles DPI scaling: screenshots are taken at physical resolution,
        but pyautogui operates in logical (DPI-scaled) coordinates.

        Args:
            x, y: Raw coordinates from the VLM
            image_size: (width, height) of the image sent to VLM
            screen_size: (width, height) for pyautogui (logical pixels)
            model_name: name of the model (for auto-detection)

        Returns:
            (screen_x, screen_y) in pyautogui's coordinate space
        """
        if screen_size is None:
            screen_size = pyautogui.size()
        sw, sh = screen_size  # pyautogui logical size

        coord_format = config.COORD_FORMAT

        if coord_format == "auto":
            # Qwen3-VL (local Ollama) uses normalized 0-1000 grid.
            # Qwen API models (qwen-vl-max, qwen-vl-plus) and Qwen2.5-VL
            # use absolute pixel coordinates matching the input image.
            model_lower = model_name.lower()
            if "qwen3" in model_lower:
                coord_format = "normalized_1000"
            else:
                coord_format = "absolute"

        if coord_format == "normalized_1000":
            # Qwen3-VL: coordinates in a 0-1000 normalized grid → map to logical screen
            real_x = round(x / 1000 * (sw - 1))
            real_y = round(y / 1000 * (sh - 1))
        elif coord_format == "absolute" and image_size:
            # Model outputs absolute pixel coordinates relative to the image.
            # The image was captured at physical resolution, but pyautogui
            # uses logical (DPI-scaled) coordinates.
            iw, ih = image_size
            # image coords → logical screen coords
            real_x = round(x / iw * sw)
            real_y = round(y / ih * sh)
        else:
            # Fallback: use raw coordinates as-is
            real_x, real_y = x, y

        # Clamp to screen bounds
        real_x = max(0, min(real_x, sw - 1))
        real_y = max(0, min(real_y, sh - 1))
        return real_x, real_y
    
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
    
    def execute_action(
        self,
        action: Dict[str, Any],
        image_size: Optional[Tuple[int, int]] = None,
        model_name: str = "",
    ) -> Tuple[bool, str]:
        """
        Execute an action from LLM response.

        Args:
            action: Action dict with 'type' and 'params'
            image_size: (width, height) of the image sent to the LLM (for coordinate conversion)
            model_name: name of the VLM model (for auto-detecting coordinate format)

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
            raw_x = params.get("x", 0)
            raw_y = params.get("y", 0)
            x, y = self.convert_coordinates(raw_x, raw_y, image_size=image_size, model_name=model_name)
            button = params.get("button", "left")
            clicks = params.get("clicks", 1)
            success = self.click(x, y, button, clicks)
            return success, f"Clicked at ({x}, {y}) [raw: ({raw_x}, {raw_y})]"

        elif action_type == "move":
            raw_x = params.get("x", 0)
            raw_y = params.get("y", 0)
            x, y = self.convert_coordinates(raw_x, raw_y, image_size=image_size, model_name=model_name)
            success = self.move(x, y)
            return success, f"Moved to ({x}, {y}) [raw: ({raw_x}, {raw_y})]"
        
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
            raw_x = params.get("x")
            raw_y = params.get("y")
            if raw_x is not None and raw_y is not None:
                x, y = self.convert_coordinates(raw_x, raw_y, image_size=image_size, model_name=model_name)
            else:
                x, y = raw_x, raw_y
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
