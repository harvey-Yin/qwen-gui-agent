"""
Orchestrator for GUI-Agent
Manages the ReAct loop: Observe -> Think -> Act -> Repeat
"""
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm.ollama_client import OllamaClient
from tools.gui_tools import GUITools
from tools.screen_capture import ScreenCapture
from agent.action_parser import ActionParser, ActionType


@dataclass
class Step:
    """A single step in the agent execution."""
    step_number: int
    screenshot_b64: str
    thought: str
    action_type: str
    action_params: Dict[str, Any]
    action_result: str
    status: str
    timestamp: float = field(default_factory=time.time)


@dataclass 
class TaskResult:
    """Result of a task execution."""
    success: bool
    message: str
    steps: List[Step]
    total_time: float


class Orchestrator:
    """
    Main orchestrator that runs the ReAct loop.
    
    Flow:
    1. User provides a task
    2. Take screenshot
    3. Send to LLM with task and screenshot
    4. Parse LLM response for action
    5. Execute action
    6. Repeat until done or max steps
    """
    
    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        gui_tools: Optional[GUITools] = None,
        screen_capture: Optional[ScreenCapture] = None,
        max_steps: int = config.MAX_STEPS,
        step_delay: float = config.STEP_DELAY,
        on_step_callback: Optional[Callable[[Step], None]] = None
    ):
        self.llm = llm_client or OllamaClient()
        self.tools = gui_tools or GUITools()
        self.screen = screen_capture or ScreenCapture()
        self.parser = ActionParser()
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.on_step_callback = on_step_callback
        
        self.current_task: Optional[str] = None
        self.steps: List[Step] = []
        self.is_running: bool = False
    
    def _build_user_message(self, task: str, step_num: int) -> str:
        """Build the user message for LLM."""
        if step_num == 1:
            return f"""任务: {task}

这是当前屏幕截图。请分析屏幕并决定第一步操作。"""
        else:
            return f"""继续执行任务: {task}

这是执行上一步操作后的屏幕截图。请分析当前状态并决定下一步。
如果任务已完成，请使用 done 动作。"""
    
    def run_task(self, task: str) -> TaskResult:
        """
        Execute a task using the ReAct loop.
        
        Args:
            task: The user's task description
            
        Returns:
            TaskResult with execution details
        """
        self.current_task = task
        self.steps = []
        self.is_running = True
        start_time = time.time()
        
        conversation_history: List[Dict[str, Any]] = []
        
        for step_num in range(1, self.max_steps + 1):
            if not self.is_running:
                break
            
            # 1. Observe - Take screenshot
            screenshot_b64 = self.screen.capture_to_base64()
            
            # 2. Think - Send to LLM
            user_message = self._build_user_message(task, step_num)
            
            llm_response = self.llm.chat_with_image(
                user_message=user_message,
                image_base64=screenshot_b64,
                history=conversation_history
            )
            
            # Parse response
            parsed = self.parser.parse(llm_response)
            
            # 3. Act - Execute action
            action_dict = {
                "type": parsed.action.type.value,
                "params": parsed.action.params
            }
            success, result_msg = self.tools.execute_action(action_dict)
            
            # Record step
            step = Step(
                step_number=step_num,
                screenshot_b64=screenshot_b64,
                thought=parsed.thought,
                action_type=parsed.action.type.value,
                action_params=parsed.action.params,
                action_result=result_msg,
                status=parsed.status
            )
            self.steps.append(step)
            
            # Callback for UI updates
            if self.on_step_callback:
                self.on_step_callback(step)
            
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            conversation_history.append({
                "role": "assistant", 
                "content": llm_response
            })
            
            # Check if done
            if parsed.status == "completed" or parsed.action.type == ActionType.DONE:
                self.is_running = False
                # Handle params safely
                params = parsed.action.params
                if isinstance(params, dict):
                    message = params.get("message", "Task completed")
                else:
                    message = str(params) if params else "Task completed"
                return TaskResult(
                    success=True,
                    message=message,
                    steps=self.steps,
                    total_time=time.time() - start_time
                )
            
            if parsed.status == "failed":
                self.is_running = False
                return TaskResult(
                    success=False,
                    message=f"Task failed: {parsed.thought}",
                    steps=self.steps,
                    total_time=time.time() - start_time
                )
            
            # Delay before next step
            time.sleep(self.step_delay)
        
        # Max steps reached
        self.is_running = False
        return TaskResult(
            success=False,
            message=f"Max steps ({self.max_steps}) reached without completion",
            steps=self.steps,
            total_time=time.time() - start_time
        )
    
    def stop(self):
        """Stop the current task execution."""
        self.is_running = False
    
    def get_steps(self) -> List[Step]:
        """Get all steps from current/last task."""
        return self.steps.copy()


if __name__ == "__main__":
    # Test orchestrator
    orchestrator = Orchestrator()
    
    # Simple test - just check if LLM is connected
    print(f"LLM connected: {orchestrator.llm.test_connection()}")
    print(f"Screen size: {orchestrator.screen.get_screen_size()}")
