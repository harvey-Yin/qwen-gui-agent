"""
WebPageInteract Skill
Finds and interacts with target elements on a web page.
"""
from typing import List, Optional
from skills.base_skill import BaseSkill


class WebPageInteractSkill(BaseSkill):
    """
    Skill: 在网页中寻找目标元素并进行交互操作。

    为 VLM 生成包含目标描述和视觉提示的精确指令，
    让 VLM 在网页截图中定位并操作目标元素。
    """

    name = "web_page_interact"
    description = "在网页中寻找目标元素并进行交互操作"
    max_steps = 8

    def build_prompt(self, **kwargs) -> str:
        """
        Generate prompt for interacting with web page elements.

        Args:
            goal (str): Natural language description of the interaction goal.
            hints (list[str], optional): Visual hints to help identify the target.
        """
        goal = kwargs.get("goal", "")
        hints: List[str] = kwargs.get("hints", [])

        if not goal:
            raise ValueError("WebPageInteractSkill requires 'goal' parameter")

        prompt = f"""你当前的子任务是：{goal}

【操作要求】
1. 仔细观察当前页面的内容和布局
2. 根据目标描述找到对应的元素
3. 如果目标元素不在当前可视区域内，使用滚动操作(scroll)查找
4. 找到目标后，执行适当的操作（单击或双击）
5. 确认操作成功后报告完成"""

        if hints:
            hint_text = "\n".join(f"  - {h}" for h in hints)
            prompt += f"""

【识别提示】
{hint_text}"""

        prompt += """

【注意事项】
- 如果页面需要登录，请先完成登录流程
- 如果页面有弹窗或遮罩层，请先关闭它们
- 如果找不到目标，可以尝试滚动页面或切换标签页
- 每次操作后观察页面变化，确认操作是否生效"""

        return prompt

    def get_system_prompt_addon(self) -> str:
        return """
【当前技能：网页元素交互】
你正在网页中寻找并操作特定元素。
仔细观察页面上的文字、图标、颜色等视觉特征来定位目标。
如果目标不在视野内，可以使用 scroll 向下滚动查找。
找到目标后使用 click 或 double_click 进行操作。
"""
