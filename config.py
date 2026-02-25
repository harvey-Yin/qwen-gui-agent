# Configuration for GUI-Agent
import os

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  LLM Provider 选择                                                 ║
# ║  "ollama"    → 本地 Ollama 服务 (Qwen3-VL:8B)                       ║
# ║  "qwen_api"  → 阿里云 DashScope API (qwen3-vl-flash)               ║
# ║  "glm_api"   → 智谱官方 zai-sdk (glm-4.6v-flash)                    ║
# ║  "glm_local" → 本地 Transformers 部署 (GLM-4.6V-Flash)              ║
# ╚══════════════════════════════════════════════════════════════════════╝
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "glm_local")

# ── 1. 本地 Ollama (Qwen3-VL:8B) ─────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

# ── 2. 阿里云 Qwen API (qwen3-vl-flash) ──────────────────────────────────────
QWEN_API_BASE_URL = os.getenv("QWEN_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "sk-4bf30eb02a044c1396c2ae329828c50f")
QWEN_API_MODEL = os.getenv("QWEN_API_MODEL", "qwen3-vl-flash")

# ── 3. 智谱 GLM API (glm-4.6v-flash) ─────────────────────────────────────────
GLM_API_KEY = os.getenv("GLM_API_KEY", "3a54b8fc6ffa49539bafd716c7922fc3.497QGYFslMmQP06D")
# 模型选项: glm-4.6v-flash (免费) | glm-4.1v-thinking | glm-4v-plus | glm-4v
GLM_API_MODEL = os.getenv("GLM_API_MODEL", "glm-4.6v-flash")

# ── 4. 本地 GLM Transformers (GLM-4.6V-Flash) ────────────────────────────────
# 模型路径: ModelScope/HuggingFace 模型 ID 或本地目录
GLM_LOCAL_MODEL_PATH = os.getenv("GLM_LOCAL_MODEL_PATH", "ZhipuAI/GLM-4.6V-Flash")
# 推理设备: "auto" (自动选择 GPU) | "cpu" | "cuda:0"
GLM_LOCAL_DEVICE = os.getenv("GLM_LOCAL_DEVICE", "auto")
# torch_dtype: "float16" (推荐, ~7GB显存) | "bfloat16" | "auto"
GLM_LOCAL_DTYPE = os.getenv("GLM_LOCAL_DTYPE", "float16")

# ── 坐标格式 ──────────────────────────────────────────────────────────────────
# "auto"            = 根据模型名自动检测 (推荐)
# "normalized_1000" = Qwen3-VL 风格 (坐标 0-1000 网格)
# "absolute"        = 绝对像素坐标 (GLM / Qwen API / Qwen2.5-VL)
COORD_FORMAT = os.getenv("COORD_FORMAT", "auto")

# ── Agent 设置 ────────────────────────────────────────────────────────────────
MAX_STEPS = 20          # 每个任务最大步骤数
STEP_DELAY = 1.0        # 步骤间等待 (秒)
SCREENSHOT_QUALITY = 85  # JPEG 截图质量

# ── PyAutoGUI 安全设置 ────────────────────────────────────────────────────────
PYAUTOGUI_PAUSE = 0.5    # PyAutoGUI 调用间隔
PYAUTOGUI_FAILSAFE = True  # 鼠标移到角落可中止

# ── Streamlit 设置 ────────────────────────────────────────────────────────────
STREAMLIT_PORT = 8501

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
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
