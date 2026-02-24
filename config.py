# Configuration for GUI-Agent
import os

# LLM Provider: "ollama" | "openai_compat"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

# OpenAI-compatible API settings (Qwen API / SiliconFlow / OpenRouter)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-4bf30eb02a044c1396c2ae329828c50f")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen3-vl-flash")

# Coordinate format output by the VLM
# "auto"            = Auto-detect based on model name (recommended)
# "normalized_1000" = Force Qwen3-VL style (coordinates in 0-1000 grid)
# "absolute"        = Force absolute pixel coordinates (Qwen API / Qwen2.5-VL)
COORD_FORMAT = os.getenv("COORD_FORMAT", "auto")

# Agent settings
MAX_STEPS = 20  # Maximum steps per task
STEP_DELAY = 1.0  # Delay between actions (seconds) - increased for stability
SCREENSHOT_QUALITY = 85  # JPEG quality for screenshots

# PyAutoGUI safety settings
PYAUTOGUI_PAUSE = 0.5  # Pause between PyAutoGUI calls
PYAUTOGUI_FAILSAFE = True  # Move mouse to corner to abort

# Streamlit settings  
STREAMLIT_PORT = 8501

# System prompt for the agent
SYSTEM_PROMPT = """/no_think
你是一个Windows GUI自动化代理。分析屏幕截图并执行操作完成任务。

【必须遵守的规则】
1. 只输出JSON，不要输出任何其他文字、解释或markdown
2. 忽略GUI Agent窗口本身，操作Windows系统和其他应用程序
3. 打开程序请使用Win+R运行对话框或点击Windows开始按钮

【JSON格式】（严格遵守，不要添加任何额外内容）
{"thought":"思考过程","action":{"type":"动作类型","params":{参数}},"status":"in_progress"}

【动作类型】
- hotkey: 按快捷键 {"keys":["win","r"]} 
- click: 单击 {"x":100,"y":200}
- double_click: 双击 {"x":100,"y":200}
- right_click: 右键点击 {"x":100,"y":200}
- type: 输入 {"text":"notepad"}
- scroll: 滚动 {"amount":3} (正数向上，负数向下)
- wait: 等待 {"seconds":1}
- done: 完成 {"message":"描述"}

【打开记事本示例】
步骤1: {"thought":"按Win+R打开运行","action":{"type":"hotkey","params":{"keys":["win","r"]}},"status":"in_progress"}
步骤2: {"thought":"输入notepad","action":{"type":"type","params":{"text":"notepad"}},"status":"in_progress"}
步骤3: {"thought":"按回车运行","action":{"type":"hotkey","params":{"keys":["enter"]}},"status":"in_progress"}
步骤4: {"thought":"记事本已打开","action":{"type":"done","params":{"message":"记事本已成功打开"}},"status":"completed"}
"""

