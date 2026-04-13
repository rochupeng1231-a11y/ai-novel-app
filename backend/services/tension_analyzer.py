"""
张力分析服务
"""
import re
from backend.config import TENSION_KEYWORDS, SHORT_SENTENCE_THRESHOLD


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
        keywords = TENSION_KEYWORDS.get("conflict", [])
        count = sum(1 for kw in keywords if kw in text)
        return min(count / 5, 1.0)

    def _analyze_suspense(self, text: str) -> float:
        """悬念程度"""
        keywords = TENSION_KEYWORDS.get("suspense", [])
        count = sum(1 for kw in keywords if kw in text)
        return min(count / 4, 1.0)

    def _analyze_emotion(self, text: str) -> float:
        """情感张力"""
        keywords = TENSION_KEYWORDS.get("emotion", [])
        count = sum(1 for kw in keywords if kw in text)
        return min(count / 5, 1.0)

    def _analyze_rhythm(self, text: str) -> float:
        """节奏密度（短句/段落越多，节奏越快）"""
        text = text.strip()
        if not text:
            return 0.0

        sentences = re.split(r'[。!?]', text)
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return 0.0

        short_sentences = sum(1 for s in sentences if len(s.strip()) < SHORT_SENTENCE_THRESHOLD)
        return min(short_sentences / len(sentences), 1.0)
