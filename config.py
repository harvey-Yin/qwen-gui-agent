# Configuration for GUI-Agent
import os

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

# Agent settings
MAX_STEPS = 20  # Maximum steps per task
STEP_DELAY = 0.5  # Delay between actions (seconds)
SCREENSHOT_QUALITY = 85  # JPEG quality for screenshots

# PyAutoGUI safety settings
PYAUTOGUI_PAUSE = 0.3  # Pause between PyAutoGUI calls
PYAUTOGUI_FAILSAFE = True  # Move mouse to corner to abort

# Streamlit settings  
STREAMLIT_PORT = 8501

# System prompt for the agent
SYSTEM_PROMPT = """你是一个 GUI 自动化代理。你可以看到屏幕截图并执行操作来完成用户任务。

每次回复必须使用以下 JSON 格式（不要包含其他文字）：
{
  "thought": "你的思考过程，分析当前屏幕状态和下一步操作",
  "action": {
    "type": "动作类型",
    "params": { 参数 }
  },
  "status": "in_progress 或 completed 或 failed"
}

可用的动作类型：
- click: 鼠标点击，参数 {"x": 数字, "y": 数字, "button": "left"或"right", "clicks": 1或2}
- move: 移动鼠标，参数 {"x": 数字, "y": 数字}
- type: 输入文本，参数 {"text": "要输入的文本"}
- hotkey: 快捷键，参数 {"keys": ["ctrl", "c"]}
- scroll: 滚动，参数 {"amount": 数字, "x": 数字, "y": 数字}
- wait: 等待，参数 {"seconds": 数字}
- done: 任务完成，参数 {"message": "完成描述"}

重要规则：
1. 仔细观察屏幕截图，确定需要点击的位置
2. 如果看到目标元素，直接返回点击该元素的坐标
3. 如果任务完成，使用 done 动作
4. 如果遇到问题无法继续，status 设为 failed 并说明原因
"""
