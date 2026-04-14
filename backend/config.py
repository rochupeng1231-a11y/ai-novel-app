"""
配置文件 - 从环境变量读取
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============ AI API 密钥 ============
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# ============ AI 参数配置 ============
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16384"))
TIMEOUT = float(os.getenv("TIMEOUT", "60"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# ============ AI Provider 端点配置 ============
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"
MINIMAX_MODEL = "MiniMax-M2.7"

KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

CLAUDE_BASE_URL = "https://api.anthropic.com"
CLAUDE_MODEL = "claude-3-haiku-20240307"

# ============ AI 聚合器配置 ============

# 模型策略：任务类型 -> provider
MODEL_STRATEGY = {
    "outline": "deepseek",
    "draft": "kimi",
    "core": "claude",
    "polish": "claude",
    "minimax": "minimax",
}

# 流式生成 fallback 顺序
STREAM_FALLBACK = ["deepseek", "minimax_anthropic", "minimax", "kimi", "claude"]

# 判断为限流的关键词
RATE_LIMIT_KEYWORDS = [
    "529", "overloaded", "rate_limit", "rate limit",
    "readtimeout", "timeout", "service unavailable",
    "overloaded_error", "request rate surge",
    "服务集群负载较高", "服务繁忙", "服务器负载"
]

# ============ 张力分析关键词配置 ============

TENSION_KEYWORDS = {
    "conflict": [
        "怒", "吼", "骂", "吵", "争", "夺", "抢", "砸",
        "凭什么", "你算什么东西", "滚", "滚出去", "动手",
        "愤怒", "暴怒", "冷笑", "对峙", "剑拔弩张",
        "争吵", "打架", "对抗", "矛盾", "冲突", "争执",
        "冷战", "对立", "争夺", "比拼", "较量"
    ],
    "suspense": [
        "突然", "忽然", "猛地", "骤然", "陡然",
        "难道", "莫非", "究竟", "到底", "如何",
        "就在这时", "就在此时", "突然发现", "没想到",
        "意想不到", "出乎意料", "然而", "但是",
        "……", "..."
    ],
    "emotion": [
        "愤怒", "悲伤", "喜悦", "恐惧", "惊讶", "心痛",
        "激动", "绝望", "希望", "爱", "恨", "不舍",
        "害怕", "恐惧", "颤抖", "流泪", "哭泣",
        "欢喜", "开心", "难过", "伤心", "生气",
        "紧握", "抓紧", "拉住", "抱住", "推开",
        "心想", "想着", "暗想", "心想道"
    ]
}

# 短句阈值（字符数）
SHORT_SENTENCE_THRESHOLD = 15

# ============ Prompt 模板配置 ============

# 默认小说类型
DEFAULT_NOVEL_TYPE = "都市言情"

# Prompt 模板
PROMPT_TEMPLATES = {
    "大纲": """你是一位专业小说家。

【当前任务】
为以下小说生成大纲，必须包含全部5个部分：

{context}

【输出格式】（必须全部完成，缺一不可）
1. 故事主线（1-2段，简短）
2. 主要人物（3-5个，用列表）
3. 章节结构（8-12章，每章一行）
4. 角色关系（表格）
5. 重要伏笔（3-5个）

【重要】未完成全部5个部分之前不要停止！""",

    "续写": """你是一位拥有20年创作经验的专业{novel_type}小说作家。

【身份设定】
你是角色本人，用角色的眼睛去看，用角色的心去感受。你不是旁观者叙述，而是角色正在经历的一切。文字要有温度、有呼吸、有心跳。

【写作风格】
- 短句和长句交替，营造阅读节奏感
- 善用动作和对话推动情节，减少冗长的心理描写
- 情感表达克制但深刻
- 环境描写点缀而非铺陈

【当前任务】
根据下方的项目背景和已有内容，续写当前章节。

{context}

【写作要求】
- 严格按照设定的{novel_type}类型和风格写作
- 严格保持角色性格一致
- 情节自然推进，不突兀
- 字数控制在800-1500字
- 续写内容要有进展感，不能原地踏步
- 结束时留下期待感，吸引继续阅读

请继续书写：""",

    "润色": """你是一位资深文学编辑，专精{novel_type}小说文字打磨。

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

    "改写": """你是一位文风多变的创意小说家，精通不同叙事风格的{novel_type}作品。

【身份设定】
你是一个善于变换叙事手法的作家，可以用不同的角度、节奏和风格重新诠释同一个故事。你对"怎么讲"和"讲什么"同样重视。

【当前任务】
用不同的叙事风格重新讲述下文的故事

原文：
{context}

【改写方向】
请选择与原文不同的叙事角度，改变句式结构和表达方式，但保持核心情节不变。

【写作要求】
- 改变叙事视角和叙述方式
- 保持所有关键情节点不变
- 创造与原文不同的阅读体验
- 字数与原文相近

请改写：""",

    "概括": """你是一位专业的小说评论家和内容分析师。

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
