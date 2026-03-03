"""
Base Workflow class for GUI-Agent.
Provides multi-step task orchestration using Skills.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from skills.base_skill import BaseSkill

if TYPE_CHECKING:
    from agent.orchestrator import Orchestrator, TaskResult, Step

logger = logging.getLogger("Workflow")


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Attributes:
        skill: The Skill to execute in this step.
        params: Parameters to pass to the skill's build_prompt().
        on_failure: Failure strategy — "abort", "retry", or "skip".
        max_retries: Number of retries when on_failure is "retry".
        description: Human-readable description of this step.
    """
    skill: BaseSkill
    params: Dict[str, Any] = field(default_factory=dict)
    on_failure: str = "abort"
    max_retries: int = 1
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = self.skill.description


class BaseWorkflow:
    """
    Base class for all Workflows.

    A Workflow is an ordered sequence of WorkflowSteps, each powered by
    a Skill. The workflow runner executes steps sequentially, passing
    each skill's prompt to the Orchestrator's run_task() method.

    Subclasses should define:
        - name (str): Workflow identifier
        - description (str): Human-readable description
        - steps (List[WorkflowStep]): Ordered list of steps
    """

    name: str = "base_workflow"
    description: str = "Base workflow"
    steps: List[WorkflowStep] = []

    def get_steps(self) -> List[WorkflowStep]:
        """
        Return the list of workflow steps.
        Override in subclasses for dynamic step generation.
        """
        return self.steps

    def run(self, orchestrator: "Orchestrator") -> "TaskResult":
        """
        Execute the workflow by running each step sequentially.

        Each step generates a focused prompt via its Skill and runs it
        through the existing Orchestrator.run_task() method.

        Args:
            orchestrator: The Orchestrator instance to execute tasks with.

        Returns:
            TaskResult with aggregated execution details.
        """
        from agent.orchestrator import TaskResult, Step

        all_steps: List[Step] = []
        start_time = time.time()
        workflow_steps = self.get_steps()

        logger.info(f"========== 工作流开始: {self.name} ==========")
        logger.info(f"描述: {self.description}")
        logger.info(f"总步骤数: {len(workflow_steps)}")

        for i, wf_step in enumerate(workflow_steps, 1):
            logger.info(f"--- 工作流步骤 {i}/{len(workflow_steps)}: "
                        f"{wf_step.description} ---")

            # Build prompt from skill
            sub_task = wf_step.skill.build_prompt(**wf_step.params)

            # Temporarily adjust orchestrator's max_steps for this skill
            original_max_steps = orchestrator.max_steps
            orchestrator.max_steps = wf_step.skill.max_steps

            # Execute with retries
            attempts = 0
            max_attempts = wf_step.max_retries + 1 if wf_step.on_failure == "retry" else 1
            result = None

            while attempts < max_attempts:
                attempts += 1
                logger.info(f"执行尝试 {attempts}/{max_attempts}")

                result = orchestrator.run_task(sub_task)
                all_steps.extend(result.steps)

                if result.success:
                    logger.info(f"步骤 {i} 成功完成")
                    break
                elif wf_step.on_failure == "retry" and attempts < max_attempts:
                    logger.warning(f"步骤 {i} 失败，准备重试...")
                    time.sleep(1)

            # Restore original max_steps
            orchestrator.max_steps = original_max_steps

            # Handle failure
            if result and not result.success:
                if wf_step.on_failure == "abort":
                    logger.error(f"步骤 {i} 失败，终止工作流")
                    return TaskResult(
                        success=False,
                        message=f"工作流在步骤 {i} ({wf_step.description}) 失败: {result.message}",
                        steps=all_steps,
                        total_time=time.time() - start_time,
                    )
                elif wf_step.on_failure == "skip":
                    logger.warning(f"步骤 {i} 失败，跳过继续")
                    continue

        total_time = time.time() - start_time
        logger.info(f"========== 工作流完成: {self.name} "
                     f"({total_time:.1f}秒) ==========")

        return TaskResult(
            success=True,
            message=f"工作流 '{self.description}' 执行完成",
            steps=all_steps,
            total_time=total_time,
        )

    def __repr__(self) -> str:
        return (f"<Workflow: {self.name} "
                f"({len(self.get_steps())} steps)>")
