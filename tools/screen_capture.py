"""
Screen Capture Tool for GUI-Agent
Handles taking screenshots and encoding them for LLM.
"""
import base64
import io
from typing import Optional, Tuple
from PIL import Image, ImageGrab
import pyautogui

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class ScreenCapture:
    """Utility for capturing and processing screenshots."""
    
    def __init__(self, quality: int = config.SCREENSHOT_QUALITY):
        self.quality = quality
    
    def capture_screen(
        self,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Image.Image:
        """
        Capture the screen or a region.
        
        Args:
            region: Optional (x, y, width, height) tuple
            
        Returns:
            PIL Image object
        """
        # Use PIL ImageGrab directly to avoid pyscreeze issues
        if region:
            # Convert (x, y, width, height) to (left, top, right, bottom)
            bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            screenshot = ImageGrab.grab(bbox=bbox)
        else:
            screenshot = ImageGrab.grab()
        return screenshot
    
    def capture_to_base64(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        max_size: Tuple[int, int] = (1920, 1080)
    ) -> Tuple[str, int, int]:
        """
        Capture screen and return as base64 encoded JPEG.

        Args:
            region: Optional region to capture
            max_size: Maximum size to resize to (for faster LLM processing)

        Returns:
            Tuple of (base64_encoded_string, image_width, image_height)
        """
        screenshot = self.capture_screen(region)

        # Resize if too large
        if screenshot.width > max_size[0] or screenshot.height > max_size[1]:
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

        img_w, img_h = screenshot.size

        # Convert to JPEG and encode
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=self.quality)
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8"), img_w, img_h
    
    def save_screenshot(
        self,
        filepath: str,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """
        Capture and save screenshot to file.
        
        Args:
            filepath: Path to save the image
            region: Optional region to capture
            
        Returns:
            The filepath
        """
        screenshot = self.capture_screen(region)
        screenshot.save(filepath)
        return filepath
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the screen resolution."""
        return pyautogui.size()


if __name__ == "__main__":
    # Test screen capture
    capture = ScreenCapture()
    print(f"Screen size: {capture.get_screen_size()}")

    # Take a test screenshot
    b64, w, h = capture.capture_to_base64()
    print(f"Screenshot captured, base64 length: {len(b64)}, image size: {w}x{h}")
