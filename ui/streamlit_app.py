"""
Streamlit Chat Interface for GUI-Agent
Provides a user-friendly chat interface for interacting with the agent.
"""
import streamlit as st
import time
import base64
from io import BytesIO
from PIL import Image
import threading
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.orchestrator import Orchestrator, Step, TaskResult
from llm import create_client
import config


def decode_base64_image(b64_string: str) -> Image.Image:
    """Decode base64 string to PIL Image."""
    image_data = base64.b64decode(b64_string)
    return Image.open(BytesIO(image_data))


def init_session_state():
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = Orchestrator()
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "current_steps" not in st.session_state:
        st.session_state.current_steps = []


def _build_client_kwargs(provider: str) -> dict:
    """Build kwargs for create_client based on the current provider and UI state."""
    if provider == "ollama":
        return {
            "base_url": st.session_state.get("api_base_url", config.OLLAMA_BASE_URL),
            "model": st.session_state.get("model_name", config.OLLAMA_MODEL),
        }
    elif provider == "qwen_api":
        return {
            "base_url": st.session_state.get("api_base_url", config.QWEN_API_BASE_URL),
            "api_key": st.session_state.get("api_key", config.QWEN_API_KEY),
            "model": st.session_state.get("model_name", config.QWEN_API_MODEL),
        }
    elif provider == "glm_api":
        return {
            "api_key": st.session_state.get("api_key", config.GLM_API_KEY),
            "model": st.session_state.get("model_name", config.GLM_API_MODEL),
        }
    elif provider == "glm_local":
        return {
            "model_path": st.session_state.get("model_path", config.GLM_LOCAL_MODEL_PATH),
            "device_map": st.session_state.get("device_map", config.GLM_LOCAL_DEVICE),
            "torch_dtype": st.session_state.get("torch_dtype", config.GLM_LOCAL_DTYPE),
        }
    return {}


def check_llm_connection() -> bool:
    """Check if the configured LLM is accessible."""
    provider = st.session_state.get("provider", config.LLM_PROVIDER)
    try:
        client = create_client(provider=provider, **_build_client_kwargs(provider))
        return client.test_connection()
    except Exception:
        return False


def run_agent_task(task: str):
    """Run agent task and update session state."""
    st.session_state.is_running = True
    st.session_state.current_steps = []

    def on_step(step: Step):
        st.session_state.current_steps.append(step)

    # Build the client from current UI settings
    provider = st.session_state.get("provider", config.LLM_PROVIDER)
    client = create_client(provider=provider, **_build_client_kwargs(provider))

    orchestrator = Orchestrator(llm_client=client, on_step_callback=on_step)
    result = orchestrator.run_task(task)

    st.session_state.is_running = False
    return result


def main():
    st.set_page_config(
        page_title="GUI Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-running {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #28a745;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #dc3545;
    }
    .thought-box {
        background-color: #e3f2fd;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
        margin: 0.5rem 0;
    }
    .action-box {
        background-color: #f3e5f5;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border-left: 4px solid #9c27b0;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">🤖 GUI Agent</p>', unsafe_allow_html=True)
    st.markdown("多模型 GUI 自动化代理（Qwen / GLM）")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ 设置")

        # ── Model Provider ──
        st.subheader("🔌 模型配置")
        provider_options = ["ollama", "qwen_api", "glm_api", "glm_local"]
        provider_labels = {
            "ollama": "① Ollama 本地 (Qwen3-VL)",
            "qwen_api": "② 阿里云 Qwen API",
            "glm_api": "③ 智谱 GLM API",
            "glm_local": "④ 本地 GLM (Transformers)",
        }
        default_idx = provider_options.index(config.LLM_PROVIDER) if config.LLM_PROVIDER in provider_options else 0
        provider = st.selectbox(
            "Provider",
            provider_options,
            index=default_idx,
            key="provider",
            format_func=lambda x: provider_labels[x],
        )

        if provider == "ollama":
            st.text_input("Ollama 地址", value=config.OLLAMA_BASE_URL, key="api_base_url")
            st.text_input("模型名称", value=config.OLLAMA_MODEL, key="model_name")

        elif provider == "qwen_api":
            st.text_input("API Base URL", value=config.QWEN_API_BASE_URL, key="api_base_url",
                          help="阿里云 DashScope 接口地址")
            st.text_input("API Key", value=config.QWEN_API_KEY, type="password", key="api_key")
            st.text_input("模型名称", value=config.QWEN_API_MODEL, key="model_name")

        elif provider == "glm_api":
            st.text_input("API Key", value=config.GLM_API_KEY, type="password", key="api_key")
            st.text_input("模型名称", value=config.GLM_API_MODEL, key="model_name",
                          help="glm-4.6v-flash / glm-4v-plus / glm-4.1v-thinking")

        elif provider == "glm_local":
            st.text_input("模型路径", value=config.GLM_LOCAL_MODEL_PATH, key="model_path",
                          help="ModelScope ID 或本地目录")
            st.text_input("设备", value=config.GLM_LOCAL_DEVICE, key="device_map",
                          help="auto / cpu / cuda:0")
            st.text_input("精度", value=config.GLM_LOCAL_DTYPE, key="torch_dtype",
                          help="float16 (~7GB) / bfloat16 / auto")

        # Connection status
        if provider != "glm_local":
            if check_llm_connection():
                st.success("✅ 模型连接正常")
            else:
                st.error("❌ 无法连接模型")
                if provider == "ollama":
                    st.info("请确保 Ollama 正在运行")
                else:
                    st.info("请检查 API Key 和接口地址")
        else:
            st.info("🖥️ 本地模型将在首次执行时加载")

        st.divider()

        # Settings
        st.subheader("代理设置")
        max_steps = st.slider("最大步数", 5, 50, 20)
        step_delay = st.slider("步骤间隔 (秒)", 0.1, 2.0, 0.5)

        st.divider()

        # Instructions
        st.subheader("📖 使用说明")
        st.markdown("""
        1. 在聊天框输入任务
        2. 代理会截图分析屏幕
        3. 自动执行 GUI 操作
        4. 查看执行过程和结果

        **示例任务:**
        - 打开记事本
        - 打开浏览器访问百度
        - 打开计算器并计算 1+1
        """)

        st.divider()

        # Stop button
        if st.session_state.is_running:
            if st.button("🛑 停止执行", type="primary"):
                st.session_state.orchestrator.stop()
                st.session_state.is_running = False
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 对话")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    if "steps" in msg:
                        with st.expander(f"查看执行步骤 ({len(msg['steps'])} 步)"):
                            for step in msg["steps"]:
                                st.markdown(f"**步骤 {step.step_number}**")
                                st.markdown(f'<div class="thought-box">💭 {step.thought}</div>', 
                                          unsafe_allow_html=True)
                                st.markdown(f'<div class="action-box">🎯 {step.action_type}: {step.action_result}</div>',
                                          unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input("输入任务...", disabled=st.session_state.is_running):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Run agent
            with st.chat_message("assistant"):
                with st.spinner("🤖 代理执行中..."):
                    result = run_agent_task(prompt)
                
                if result.success:
                    st.success(f"✅ {result.message}")
                else:
                    st.error(f"❌ {result.message}")
                
                st.info(f"⏱️ 执行时间: {result.total_time:.1f}秒, 步骤数: {len(result.steps)}")
                
                # Show steps
                if result.steps:
                    with st.expander("查看执行步骤"):
                        for step in result.steps:
                            st.markdown(f"**步骤 {step.step_number}**")
                            col_a, col_b = st.columns([1, 1])
                            with col_a:
                                st.markdown(f"💭 **思考:** {step.thought}")
                            with col_b:
                                st.markdown(f"🎯 **动作:** {step.action_type}")
                                st.markdown(f"📝 **结果:** {step.action_result}")
            
            # Save assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.message,
                "steps": result.steps
            })
    
    with col2:
        st.subheader("📸 实时状态")
        
        # Show current screenshot
        if st.session_state.current_steps:
            latest_step = st.session_state.current_steps[-1]
            try:
                img = decode_base64_image(latest_step.screenshot_b64)
                st.image(img, caption=f"步骤 {latest_step.step_number} 截图", use_container_width=True)
            except Exception as e:
                st.warning(f"无法显示截图: {e}")
        else:
            st.info("执行任务后将显示屏幕截图")
        
        # Current status
        if st.session_state.is_running:
            st.markdown('<div class="status-box status-running">⏳ 执行中...</div>', 
                       unsafe_allow_html=True)
            if st.session_state.current_steps:
                step = st.session_state.current_steps[-1]
                st.markdown(f"**当前步骤:** {step.step_number}")
                st.markdown(f"**思考:** {step.thought[:100]}...")


if __name__ == "__main__":
    main()
