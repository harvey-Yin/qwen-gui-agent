"""
WaitForPageLoad Skill
Waits for a web page to finish loading.
"""
from skills.base_skill import BaseSkill


class WaitForPageLoadSkill(BaseSkill):
    """
    Skill: 等待网页加载完成。

    生成一个等待并观察页面状态的指令。
    VLM 通过截图判断页面是否已加载完毕。
    """

    name = "wait_for_page_load"
    description = "等待网页加载完成"
    max_steps = 3

    def build_prompt(self, **kwargs) -> str:
        """
        Generate prompt for waiting for page load.

        Args:
            timeout (int, optional): Max wait time in seconds. Default 5.
            description (str, optional): Description of the page being loaded.
        """
        timeout = kwargs.get("timeout", 5)
        description = kwargs.get("description", "当前页面")

        return f"""你当前的子任务是：等待{description}加载完成

【操作步骤】
1. 先等待 {timeout} 秒，让页面充分加载
2. 观察页面是否已经完成加载（页面内容已显示，没有加载中的动画或提示）
3. 如果页面已加载完成，报告完成
4. 如果页面仍在加载中（有转圈动画、进度条或"加载中"提示），再等待几秒后重新观察

【判断标准】
- 页面主要内容区域已显示
- 没有全屏的加载遮罩或转圈动画
- 浏览器标签页不再显示加载图标"""

    def get_system_prompt_addon(self) -> str:
        return """
【当前技能：等待页面加载】
你正在等待页面加载完成。
使用 wait 操作等待指定时间，然后观察截图判断页面是否加载完毕。
如果页面已经加载完成（可以看到正常的页面内容），使用 done 报告完成。
"""
