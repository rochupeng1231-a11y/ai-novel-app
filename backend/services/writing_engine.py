"""
写作引擎 - 核心服务
"""
import re
from typing import Optional, Dict, List

from backend.config import PROMPT_TEMPLATES, DEFAULT_NOVEL_TYPE, MINIMAX_API_KEY, KIMI_API_KEY, DEEPSEEK_API_KEY, CLAUDE_API_KEY
from backend.services.tension_analyzer import TensionAnalyzer
from backend.services.ai_client import ai_aggregator


class WritingEngine:
    """写作引擎，处理续写/润色/改写/概括"""

    # 任务类型映射
    TASK_TYPE_MAP = {
        "大纲": "outline",
        "续写": "draft",
        "润色": "polish",
        "改写": "polish",
        "概括": "outline"
    }

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
        def is_valid_key(key):
            return key and key not in ("your-api-key", "your_api_key_here", "your-kimi-api-key-here", "")

        return any([
            is_valid_key(MINIMAX_API_KEY),
            is_valid_key(KIMI_API_KEY),
            is_valid_key(DEEPSEEK_API_KEY),
            is_valid_key(CLAUDE_API_KEY)
        ])

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
            task_type = self.TASK_TYPE_MAP.get(instruction, "draft")
            prompt = self._build_prompt(instruction, context or "")

            if self._has_valid_api_key():
                if MINIMAX_API_KEY:
                    result_text, model_name = await ai_aggregator.generate("minimax", prompt)
                else:
                    result_text, model_name = await ai_aggregator.generate(task_type, prompt)

                result = {
                    "content": result_text,
                    "tension_score": self.tension_analyzer.analyze(result_text)["overall"],
                    "tokens_used": len(result_text) // 4
                }
            else:
                result = {
                    "content": f"[模拟{instruction}结果]\n\n此处为AI生成的文本内容...\n\n（当前未配置API密钥）",
                    "tension_score": 0.75,
                    "tokens_used": 500
                }

            self.tasks[task_id]["status"] = "completed"
            return result

        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            raise e

    def stop_task(self, task_id: str) -> bool:
        """停止指定任务"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "stopped"
            return True
        return False

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def analyze_tension_detailed(self, content: str, chapter_context: str = "") -> dict:
        """详细张力分析 + 改进建议"""
        analysis = self.tension_analyzer.analyze(content)

        issues = []

        # 冲突分析
        if analysis["conflict"] < 0.3:
            issues.append({"dimension": "冲突", "score": analysis["conflict"], "level": "低", "suggestion": "建议增加角色间的矛盾对抗，如争吵、竞争或立场冲突。"})
        elif analysis["conflict"] >= 0.7:
            issues.append({"dimension": "冲突", "score": analysis["conflict"], "level": "高", "suggestion": "冲突密度较高，注意节奏把控，避免让读者产生疲劳感。"})

        # 悬念分析
        if analysis["suspense"] < 0.3:
            issues.append({"dimension": "悬念", "score": analysis["suspense"], "level": "低", "suggestion": "建议增加悬念设置，如埋下伏笔、设置疑问或使用'突然'等转折词。"})
        elif analysis["suspense"] >= 0.7:
            issues.append({"dimension": "悬念", "score": analysis["suspense"], "level": "高", "suggestion": "悬念设置充足，注意在适当时机揭晓答案。"})

        # 情感分析
        if analysis["emotion"] < 0.3:
            issues.append({"dimension": "情感", "score": analysis["emotion"], "level": "低", "suggestion": "建议增加情感描写，如内心独白、情绪反应或角色间的情感互动。"})
        elif analysis["emotion"] >= 0.7:
            issues.append({"dimension": "情感", "score": analysis["emotion"], "level": "高", "suggestion": "情感充沛，注意情感宣泄的节奏，避免过于煽情。"})

        # 节奏分析
        if analysis["rhythm"] < 0.3:
            issues.append({"dimension": "节奏", "score": analysis["rhythm"], "level": "慢", "suggestion": "节奏较慢，建议增加短句使用，多分段。"})
        elif analysis["rhythm"] >= 0.7:
            issues.append({"dimension": "节奏", "score": analysis["rhythm"], "level": "快", "suggestion": "节奏较快，在高潮后适当放慢节奏，给读者喘息空间。"})

        overall_level = "良好" if analysis["overall"] >= 0.5 else "需改进"

        return {
            "scores": {
                "冲突": round(analysis["conflict"], 2),
                "悬念": round(analysis["suspense"], 2),
                "情感": round(analysis["emotion"], 2),
                "节奏": round(analysis["rhythm"], 2),
                "综合": round(analysis["overall"], 2)
            },
            "overall_level": overall_level,
            "issues": issues,
            "word_count": len(content),
            "summary": self._generate_summary(analysis)
        }

    def _generate_summary(self, analysis: dict) -> str:
        """生成综合评语"""
        if analysis["overall"] >= 0.7:
            return "张力充沛，是一段精彩的文本！情节紧凑，人物冲突鲜明。"
        elif analysis["overall"] >= 0.5:
            return "张力适中，可以继续打磨细节，让情节更加扣人心弦。"
        elif analysis["overall"] >= 0.3:
            return "张力偏弱，建议增加冲突和悬念，让故事更有看点。"
        else:
            return "张力不足，建议大幅调整结构，增加戏剧性冲突。"
