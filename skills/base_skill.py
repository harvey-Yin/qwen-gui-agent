"""
Base Skill class for GUI-Agent.
All skills inherit from this class and provide structured prompt generation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSkill(ABC):
    """
    Base class for all Skills.

    A Skill is a reusable atomic capability that generates a focused prompt
    for the VLM to execute. Skills do not bypass the VLM decision loop —
    they provide more precise sub-task instructions to improve success rate.

    Subclasses must implement:
        - build_prompt(**kwargs) -> str
    """

    name: str = "base_skill"
    description: str = "Base skill"
    max_steps: int = 5

    def __init__(self, max_steps: Optional[int] = None):
        if max_steps is not None:
            self.max_steps = max_steps

    @abstractmethod
    def build_prompt(self, **kwargs) -> str:
        """
        Generate a focused task prompt for the VLM.

        The prompt should be clear, step-by-step, and scoped to this
        skill's specific capability. It will be passed to
        Orchestrator.run_task() for execution.

        Args:
            **kwargs: Skill-specific parameters (e.g., url, goal, hints)

        Returns:
            A task description string for the VLM.
        """
        raise NotImplementedError

    def get_system_prompt_addon(self) -> str:
        """
        Optional additional system prompt context for this skill.
        Override in subclasses to inject skill-specific knowledge
        into the VLM's system prompt.

        Returns:
            Additional system prompt text, or empty string.
        """
        return ""

    def verify(self, screenshot_b64: str = "", **kwargs) -> bool:
        """
        Verify whether this skill was executed successfully.

        Default implementation always returns True (trust the VLM's
        "done" signal). Override for more robust verification.

        Args:
            screenshot_b64: Base64-encoded screenshot after execution
            **kwargs: Additional verification context

        Returns:
            True if skill completed successfully.
        """
        return True

    def __repr__(self) -> str:
        return f"<Skill: {self.name} (max_steps={self.max_steps})>"
