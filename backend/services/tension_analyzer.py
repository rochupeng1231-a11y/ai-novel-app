"""
张力分析服务
"""
import re


class TensionAnalyzer:
    """分析文本张力：冲突/悬念/情感/节奏"""
    
    def analyze(self, text: str) -> dict:
        """
        分析文本张力
        返回: {conflict, suspense, emotion, rhythm, overall}
        """
        conflict = self._analyze_conflict(text)
        suspense = self._analyze_suspense(text)
        emotion = self._analyze_emotion(text)
        rhythm = self._analyze_rhythm(text)
        
        overall = (conflict + suspense + emotion + rhythm) / 4
        
        return {
            "conflict": conflict,
            "suspense": suspense,
            "emotion": emotion,
            "rhythm": rhythm,
            "overall": overall
        }
    
    def _analyze_conflict(self, text: str) -> float:
        """冲突强度"""
        conflict_keywords = [
            # 对抗性动词
            "怒", "吼", "骂", "吵", "争", "夺", "抢", "砸",
            # 对抗性短语
            "凭什么", "你算什么东西", "滚", "滚出去", "动手",
            # 对抗性形容词
            "愤怒", "暴怒", "冷笑", "对峙", "剑拔弩张",
            # 名词
            "争吵", "打架", "对抗", "矛盾", "冲突", "争执",
            "冷战", "对立", "争夺", "比拼", "较量", "对峙"
        ]
        count = sum(1 for kw in conflict_keywords if kw in text)
        return min(count / 5, 1.0)
    
    def _analyze_suspense(self, text: str) -> float:
        """悬念程度"""
        suspense_keywords = [
            # 转折词
            "突然", "忽然", "猛地", "骤然", "陡然",
            # 疑问词
            "难道", "莫非", "究竟", "到底", "如何",
            # 悬念短语
            "就在这时", "就在此时", "突然发现", "没想到",
            "意想不到", "出乎意料", "然而", "但是",
            # 省略号制造悬念
            "……", "..."
        ]
        count = sum(1 for kw in suspense_keywords if kw in text)
        return min(count / 4, 1.0)
    
    def _analyze_emotion(self, text: str) -> float:
        """情感张力"""
        emotion_keywords = [
            # 情感词
            "愤怒", "悲伤", "喜悦", "恐惧", "惊讶", "心痛",
            "激动", "绝望", "希望", "爱", "恨", "不舍",
            "害怕", "恐惧", "颤抖", "流泪", "哭泣",
            "欢喜", "开心", "难过", "伤心", "生气",
            # 情感动作
            "紧握", "抓紧", "拉住", "抱住", "推开",
            # 心理描写
            "心想", "想着", "暗想", "心想道"
        ]
        count = sum(1 for kw in emotion_keywords if kw in text)
        return min(count / 5, 1.0)
    
    def _analyze_rhythm(self, text: str) -> float:
        """节奏密度（短句/段落越多，节奏越快）"""
        # 清理空白文本
        text = text.strip()
        if not text:
            return 0.0
        
        sentences = re.split(r'[。!?]', text)
        # 过滤空字符串
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return 0.0
        
        short_sentences = sum(1 for s in sentences if len(s.strip()) < 15)
        return min(short_sentences / len(sentences), 1.0)
