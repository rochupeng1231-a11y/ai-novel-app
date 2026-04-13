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
                "大纲": "outline",
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
            
            # 检查是否有有效API密钥（排除占位符）
            def is_valid_key(key):
                return key and key != "your-api-key" and key != "your_api_key_here" and key != "your-kimi-api-key-here"

            has_api = any([
                is_valid_key(os.getenv("MINIMAX_API_KEY")),
                is_valid_key(os.getenv("KIMI_API_KEY")),
                is_valid_key(os.getenv("DEEPSEEK_API_KEY")),
                is_valid_key(os.getenv("CLAUDE_API_KEY"))
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
            "大纲": f"""你是一位拥有20年创作经验的专业小说家，精通各类题材的都市言情作品。

【身份设定】
你是一位顶级都市言情小说作家，擅长细腻的情感刻画、扣人心弦的情节设计和鲜活的人物塑造。你的文字富有画面感，对话自然流畅，内心描写深入人心。

【核心原则】
- 写作时将自己代入角色，以角色的视角去感受和行动
- 情节发展要符合人物性格和故事逻辑
- 情感表达要细腻但不做作，克制但不失深情
- 场景描写要简洁有力，避免冗长的环境铺陈

【当前任务】
请为以下类型和元素的小说生成完整大纲。

{context}

【输出格式】
请严格按照以下格式输出：
1. **故事主线**（用简短的段落描述核心故事线和主题）
2. **主要人物**（3-5个角色，每个角色包含：姓名、年龄、身份、性格特点、人物弧光）
3. **章节结构**（10-15章，每章用"第X章：章节名"格式，简要描述本章核心事件）
4. **重要情节点**（标注3-5个全书最关键的剧情转折点）

请开始生成：""",

            "续写": f"""你是一位拥有20年创作经验的专业都市言情小说家。

【身份设定】
你是角色本人，用角色的眼睛去看，用角色的心去感受。你不是旁观者叙述，而是角色正在经历的一切。文字要有温度、有呼吸、有心跳。

【写作风格】
- 短句和长句交替，营造阅读节奏感
- 善用动作和对话推动情节，减少冗长的心理描写
- 情感表达克制但深刻，一个眼神胜过千言万语
- 环境描写点缀而非铺陈，服务于情绪而非堆砌词藻

【当前任务】
根据已有的故事内容，续写接下来的情节。

已有内容：
{context}

【写作要求】
- 严格保持角色性格一致
- 情节自然推进，不突兀
- 字数控制在800-1500字
- 续写内容要有进展感，不能原地踏步
- 结束时留下期待感，吸引继续阅读

请继续书写：""",

            "润色": f"""你是一位资深文学编辑，专精都市言情小说文字打磨。

【身份设定】
你是一个对文字有洁癖的编辑，每一个多余的字、每一句虚假的情感、每一个生硬的转折都逃不过你的眼睛。你的工作是让文字更精准、更动人、更有生命力。

【编辑原则】
- 删除一切冗余：重复的修饰、无意义的副词、可有可无的形容词
- 强化情感张力：该爆发的地方爆发，该压抑的地方克制
- 改善句式：避免一连串相同的句式结构，让节奏流动起来
- 保留原文风格：不改变作者的声音，只提升文字质量
- 对话要像对话：自然、口语化、有性格

【当前任务】
对下文进行精修润色

原文：
{context}

【输出要求】
- 直接输出润色后的完整内容，不要添加说明
- 保持原文段落结构和核心信息
- 字数可略有变化但不要大幅增减
- 去除"AI写作感"，让文字像真人写的

请润色：""",

            "改写": f"""你是一位文风多变的创意小说家，精通不同叙事风格的都市言情作品。

【身份设定】
你是一个善于变换叙事手法的作家，可以用不同的角度、节奏和风格重新诠释同一个故事。你对"怎么讲"和"讲什么"同样重视。

【当前任务】
用不同的叙事风格重新讲述下文的故事

原文：
{context}

【改写方向】
请选择与原文不同的叙事角度（如：第一人称↔第三人称、全知视角↔限制视角、倒叙↔正序），改变句式结构和表达方式，但保持核心情节不变。

【写作要求】
- 改变叙事视角和叙述方式
- 保持所有关键情节点不变
- 创造与原文不同的阅读体验
- 字数与原文相近
- 让读者感受到"同一个故事，不同的精彩"

请改写：""",

            "概括": f"""你是一位专业的小说评论家和内容分析师。

【身份设定】
你能够快速把握故事的精髓，用精准的语言概括核心内容。你既是故事的阅读者，也是故事的解构者。

【当前任务】
概括下文的核心内容

原文：
{context}

【概括要求】
- 提取核心情节（发生了什么）
- 保留关键细节（哪些细节对故事重要）
- 标注情感主线（读者感受到什么）
- 语言简洁精炼，用最少的字说清最多的内容
- 控制在200字以内

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
