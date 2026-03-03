"""
OpenBrowserUrl Skill
Opens the system default browser and navigates to a specified URL.
"""
from skills.base_skill import BaseSkill


class OpenBrowserUrlSkill(BaseSkill):
    """
    Skill: 打开浏览器并导航到指定 URL。

    使用 Win+R 运行对话框来启动默认浏览器访问目标网址。
    VLM 负责识别运行对话框并执行输入操作。
    """

    name = "open_browser_url"
    description = "打开浏览器并导航到指定 URL"
    max_steps = 5

    def build_prompt(self, **kwargs) -> str:
        """
        Generate prompt for opening a URL in the browser.

        Args:
            url (str): The URL to navigate to.
        """
        url = kwargs.get("url", "")
        if not url:
            raise ValueError("OpenBrowserUrlSkill requires 'url' parameter")

        return f"""你当前的子任务是：打开浏览器并导航到 {url}

【操作步骤】
1. 按 Win+R 打开"运行"对话框
2. 在"运行"对话框中输入: {url}
3. 按回车键确认
4. 等待浏览器窗口出现并开始加载页面
5. 确认浏览器已打开并显示页面内容后，报告完成

【注意事项】
- 如果浏览器已经打开，可以在地址栏中直接输入网址
- 确保输入的网址完整且正确
- 页面不需要完全加载完成，只要浏览器窗口出现即可报告完成"""

    def get_system_prompt_addon(self) -> str:
        return """
【当前技能：打开浏览器】
你正在执行"打开浏览器导航到网址"的操作。
优先使用 Win+R 运行对话框来打开网址。
如果运行对话框已打开，直接输入网址并回车。
如果浏览器已打开，可以点击地址栏后输入网址。
"""
