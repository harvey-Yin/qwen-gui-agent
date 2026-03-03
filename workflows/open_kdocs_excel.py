"""
Open KDocs Latest Excel Workflow
Opens Kingsoft Cloud Documents (金山云文档) web version and navigates to the
most recently modified online Excel spreadsheet.
"""
from workflows.base_workflow import BaseWorkflow, WorkflowStep
from skills.open_browser_url.skill import OpenBrowserUrlSkill
from skills.wait_for_page_load.skill import WaitForPageLoadSkill
from skills.web_page_interact.skill import WebPageInteractSkill


class OpenKDocsExcelWorkflow(BaseWorkflow):
    """
    工作流：打开金山云文档网页版并打开最新的在线 Excel 文件。

    流程：
    1. 打开浏览器，导航到 https://www.kdocs.cn
    2. 等待页面加载完成
    3. 在文档列表中找到最近修改的 Excel 文件并打开
    4. 等待 Excel 编辑器加载完成
    """

    name = "open_kdocs_latest_excel"
    description = "打开金山云文档网页版并打开最新的在线 Excel 文件"

    def __init__(self):
        self.steps = [
            # Step 1: 打开浏览器导航到金山文档
            WorkflowStep(
                skill=OpenBrowserUrlSkill(max_steps=5),
                params={"url": "https://www.kdocs.cn"},
                on_failure="abort",
                description="打开浏览器并导航到金山云文档 (kdocs.cn)",
            ),
            # Step 2: 等待页面加载
            WorkflowStep(
                skill=WaitForPageLoadSkill(max_steps=3),
                params={
                    "timeout": 5,
                    "description": "金山云文档首页",
                },
                on_failure="retry",
                max_retries=1,
                description="等待金山云文档首页加载完成",
            ),
            # Step 3: 找到并打开最新的 Excel 文件
            WorkflowStep(
                skill=WebPageInteractSkill(max_steps=10),
                params={
                    "goal": (
                        "在金山云文档页面中找到最近修改的 Excel 表格文件并点击打开。"
                        "如果需要登录，请先完成登录。"
                        "登录后，在文档列表中找到最近编辑的 Excel 文件，点击打开它。"
                    ),
                    "hints": [
                        "Excel/表格 文件的图标通常是绿色的表格图标",
                        "文件列表默认按最近修改时间排序，最新的文件在最上面",
                        "可能需要点击'最近'或'最近使用'标签来查看最近的文件",
                        "文件名旁边可能会标注'表格'或有 Excel 的图标标识",
                        "如果看到登录页面，需要先使用账号密码或扫码登录",
                    ],
                },
                on_failure="retry",
                max_retries=1,
                description="在文档列表中找到最新的 Excel 文件并打开",
            ),
            # Step 4: 等待 Excel 编辑器加载
            WorkflowStep(
                skill=WaitForPageLoadSkill(max_steps=3),
                params={
                    "timeout": 5,
                    "description": "Excel 在线编辑器",
                },
                on_failure="skip",
                description="等待 Excel 在线编辑器加载完成",
            ),
        ]
