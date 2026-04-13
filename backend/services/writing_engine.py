"""
写作引擎 - 核心服务
"""
import asyncio
import os
from typing import Optional, Dict, List
from backend.services.tension_analyzer import TensionAnalyzer
from backend.services.ai_client import ai_aggregator


class WritingEngine:
    """写作引擎，处理续写/润色/改写/概括"""
    
    def __init__(self):
        self.tension_analyzer = TensionAnalyzer()
        self.tasks: Dict[str, dict] = {}
    
    async def execute(self, chapter_id: str, instruction: str, context: str = None):
        """
        执行写作任务
        """
        # 生成任务ID
        task_id = f"{chapter_id}_{instruction}_{id(asyncio.current_task())}"
        
        # 记录任务状态
        self.tasks[task_id] = {
            "chapter_id": chapter_id,
            "instruction": instruction,
            "status": "running",
            "progress": 0
        }
        
        try:
            # 根据指令类型选择任务类型
            task_type_map = {
                "续写": "draft",
                "润色": "polish",
                "改写": "polish",
                "概括": "outline"
            }
            task_type = task_type_map.get(instruction, "draft")
            
            # 构建Prompt
            prompt = self._build_prompt(instruction, context or "")
            
            # 模拟进度更新（实际API调用时可以去掉）
            for i in range(3):
                if self.tasks[task_id]["status"] == "stopped":
                    return {
                        "content": "[写作被中断]",
                        "tension_score": 0.5,
                        "tokens_used": 0
                    }
                await asyncio.sleep(0.3)
                self.tasks[task_id]["progress"] = (i + 1) * 20
            
            # 检查是否有API密钥
            has_api = any([
                os.getenv("MINIMAX_API_KEY"),
                os.getenv("KIMI_API_KEY"),
                os.getenv("DEEPSEEK_API_KEY"),
                os.getenv("CLAUDE_API_KEY")
            ])
            
            if has_api:
                # 调用真实AI API
                # 优先使用MiniMax（用户已有）
                if os.getenv("MINIMAX_API_KEY"):
                    result_text, model_name = await ai_aggregator.generate("minimax", prompt)
                else:
                    result_text, model_name = await ai_aggregator.generate(task_type, prompt)
                
                result = {
                    "content": result_text,
                    "tension_score": self.tension_analyzer.analyze(result_text)["overall"],
                    "tokens_used": len(result_text) // 4  # 粗略估算
                }
            else:
                # 模拟返回（无API密钥时）
                result = {
                    "content": f"[模拟{instruction}结果]\n\n此处为AI生成的文本内容...\n\n（当前未配置API密钥，请设置 MINIMAX_API_KEY）",
                    "tension_score": 0.75,
                    "tokens_used": 500
                }
            
            self.tasks[task_id]["status"] = "completed"
            return result
            
        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            raise e
    
    def _build_prompt(self, instruction: str, context: str) -> str:
        """构建写作Prompt"""
        prompts = {
            "续写": f"""你是一位专业的小说作家，请根据下文续写故事。

写作要求：
- 保持文风一致
- 情节自然流畅
- 避免重复已有内容
- 控制字数在500-1000字

已有内容：
{context}

请续写：""",

            "润色": f"""你是一位专业的小说编辑，请对下文进行润色。

润色要求：
- 改善句式变化
- 增加文字感染力
- 保持原意不变
- 去除AI写作感

原文：
{context}

请润色：""",

            "改写": f"""你是一位专业的小说作家，请用不同风格重写下文。

改写要求：
- 改变叙述方式
- 保持核心情节
- 创造新鲜感
- 控制字数相近

原文：
{context}

请改写：""",

            "概括": f"""你是一位专业的小说编辑，请概括下文的核心内容。

概括要求：
- 提取关键情节
- 保留重要细节
- 语言简洁精炼

原文：
{context}

请概括："""
        }
        return prompts.get(instruction, prompts["续写"])
    
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
        """
        详细张力分析 + 改进建议
        """
        analysis = self.tension_analyzer.analyze(content)
        
        issues = []
        suggestions = []
        
        # 冲突分析
        if analysis["conflict"] < 0.3:
            issues.append({
                "dimension": "冲突",
                "score": analysis["conflict"],
                "level": "低",
                "suggestion": "建议增加角色间的矛盾对抗，如争吵、竞争或立场冲突。可以在关键情节处加入紧张的对峙场面。"
            })
        elif analysis["conflict"] >= 0.7:
            issues.append({
                "dimension": "冲突",
                "score": analysis["conflict"],
                "level": "高",
                "suggestion": "冲突密度较高，注意节奏把控，避免让读者产生疲劳感。"
            })
        
        # 悬念分析
        if analysis["suspense"] < 0.3:
            issues.append({
                "dimension": "悬念",
                "score": analysis["suspense"],
                "level": "低",
                "suggestion": "建议增加悬念设置，如埋下伏笔、设置疑问或使用'突然'等转折词引导读者好奇。"
            })
        elif analysis["suspense"] >= 0.7:
            issues.append({
                "dimension": "悬念",
                "score": analysis["suspense"],
                "level": "高",
                "suggestion": "悬念设置充足，注意在适当时机揭晓答案，避免过度吊胃口。"
            })
        
        # 情感分析
        if analysis["emotion"] < 0.3:
            issues.append({
                "dimension": "情感",
                "score": analysis["emotion"],
                "level": "低",
                "suggestion": "建议增加情感描写，如内心独白、情绪反应或角色间的情感互动。"
            })
        elif analysis["emotion"] >= 0.7:
            issues.append({
                "dimension": "情感",
                "score": analysis["emotion"],
                "level": "高",
                "suggestion": "情感充沛，注意情感宣泄的节奏，避免过于煽情。"
            })
        
        # 节奏分析
        if analysis["rhythm"] < 0.3:
            issues.append({
                "dimension": "节奏",
                "score": analysis["rhythm"],
                "level": "慢",
                "suggestion": "节奏较慢，建议增加短句使用，多分段，或在关键情节点使用急促的描写。"
            })
        elif analysis["rhythm"] >= 0.7:
            issues.append({
                "dimension": "节奏",
                "score": analysis["rhythm"],
                "level": "快",
                "suggestion": "节奏较快，在高潮后适当放慢节奏，给读者喘息空间。"
            })
        
        # 综合评分
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
            "summary": self._generate_summary(analysis, issues)
        }
    
    def _generate_summary(self, analysis: dict, issues: List[dict]) -> str:
        """生成综合评语"""
        if analysis["overall"] >= 0.7:
            return "张力充沛，是一段精彩的文本！情节紧凑，人物冲突鲜明。"
        elif analysis["overall"] >= 0.5:
            return "张力适中，可以继续打磨细节，让情节更加扣人心弦。"
        elif analysis["overall"] >= 0.3:
            return "张力偏弱，建议增加冲突和悬念，让故事更有看点。"
        else:
            return "张力不足，建议大幅调整结构，增加戏剧性冲突。"
