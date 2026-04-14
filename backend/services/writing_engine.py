"""
写作引擎 - 核心服务
"""
import re
from typing import Optional, Dict, List

from backend.config import PROMPT_TEMPLATES, DEFAULT_NOVEL_TYPE, MINIMAX_API_KEY
from backend.services.tension_analyzer import TensionAnalyzer
from backend.services.ai_client import mini_max_client


class WritingEngine:
    """写作引擎，处理续写/润色/改写/概括"""

    def __init__(self):
        self.tension_analyzer = TensionAnalyzer()
        self.tasks: Dict[str, dict] = {}

    def _build_prompt(self, instruction: str, context: str) -> str:
        """构建写作Prompt"""
        # 从上下文中提取小说类型
        novel_type = DEFAULT_NOVEL_TYPE
        if "【小说类型】" in context:
            match = re.search(r"【小说类型】\s*(.+?)(?:\n|$)", context)
            if match:
                novel_type = match.group(1).strip()

        # 获取模板
        template = PROMPT_TEMPLATES.get(instruction, PROMPT_TEMPLATES.get("续写", ""))

        # 填充模板
        return template.format(novel_type=novel_type, context=context)

    def _has_valid_api_key(self) -> bool:
        """检查是否有有效的API密钥"""
        return bool(MINIMAX_API_KEY and MINIMAX_API_KEY not in ("your-api-key", "your_api_key_here", ""))

    async def execute(self, chapter_id: str, instruction: str, context: str = None):
        """执行写作任务（非流式）"""
        task_id = f"{chapter_id}_{instruction}"

        self.tasks[task_id] = {
            "chapter_id": chapter_id,
            "instruction": instruction,
            "status": "running",
            "progress": 0
        }

        try:
            prompt = self._build_prompt(instruction, context or "")

            if self._has_valid_api_key():
                result_text = await mini_max_client.generate(prompt)

                result = {
                    "content": result_text,
                    "tension_score": self.tension_analyzer.analyze(result_text)["overall"],
                    "tokens_used": len(result_text) // 4
                }
            else:
                result = {
                    "content": "请配置 MiniMax API Key",
                    "tension_score": 0,
                    "tokens_used": 0
                }

            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "result": result
            })

            return result

        except Exception as e:
            self.tasks[task_id].update({
                "status": "failed",
                "error": str(e)
            })
            raise

    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "stopped"
            return True
        return False

    def get_task_status(self, task_id: str):
        """获取任务状态"""
        return self.tasks.get(task_id)