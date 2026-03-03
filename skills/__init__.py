"""
Skills module for GUI-Agent.
Provides reusable skill components for workflow orchestration.
"""
from skills.base_skill import BaseSkill
from skills.open_browser_url.skill import OpenBrowserUrlSkill
from skills.web_page_interact.skill import WebPageInteractSkill
from skills.wait_for_page_load.skill import WaitForPageLoadSkill

# Skill registry for discovery
SKILL_REGISTRY = {
    "open_browser_url": OpenBrowserUrlSkill,
    "web_page_interact": WebPageInteractSkill,
    "wait_for_page_load": WaitForPageLoadSkill,
}


def get_skill(name: str, **kwargs) -> BaseSkill:
    """Get a skill instance by name."""
    if name not in SKILL_REGISTRY:
        raise ValueError(f"Unknown skill: {name}. Available: {list(SKILL_REGISTRY.keys())}")
    return SKILL_REGISTRY[name](**kwargs)


def list_skills() -> list:
    """List all available skill names."""
    return list(SKILL_REGISTRY.keys())
