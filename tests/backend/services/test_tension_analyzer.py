"""
张力分析服务 - 单元测试
"""
import pytest
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.services.tension_analyzer import TensionAnalyzer


class TestTensionAnalyzer:
    """张力分析器测试"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.analyzer = TensionAnalyzer()
    
    def test_analyze_returns_all_dimensions(self):
        """测试返回所有维度"""
        result = self.analyzer.analyze("测试文本")
        
        assert 'conflict' in result
        assert 'suspense' in result
        assert 'emotion' in result
        assert 'rhythm' in result
        assert 'overall' in result
    
    def test_conflict_high_density(self):
        """测试冲突密度高的文本"""
        text = "两人争吵不休，对抗激烈，矛盾升级，最后大打出手"
        result = self.analyzer.analyze(text)
        
        assert result['conflict'] > 0.5
    
    def test_conflict_low_density(self):
        """测试冲突密度低的文本"""
        text = "今天天气很好，阳光明媚"
        result = self.analyzer.analyze(text)
        
        assert result['conflict'] < 0.5
    
    def test_suspense_with_keywords(self):
        """测试含悬念关键词的文本"""
        text = "突然，他发现了一个秘密，难道这就是真相？"
        result = self.analyzer.analyze(text)
        
        assert result['suspense'] > 0.3
    
    def test_emotion_high_density(self):
        """测试情感密度高的文本"""
        text = "她愤怒地尖叫，心痛欲绝，悲伤地哭泣"
        result = self.analyzer.analyze(text)
        
        assert result['emotion'] > 0.5
    
    def test_rhythm_fast(self):
        """测试快节奏（短句多）"""
        text = "跑。跳。翻。落地。"
        result = self.analyzer.analyze(text)
        
        assert result['rhythm'] > 0.5
    
    def test_rhythm_slow(self):
        """测试慢节奏（长句多）"""
        # 一个没有标点的长句
        text = "这是一个非常长的句子里面包含了很多很多的描述性词语描述着各种各样的事情和人物的心理活动"
        result = self.analyzer.analyze(text)
        
        # 单句无标点，rhythm为0
        assert result['rhythm'] == 0.0
    
    def test_overall_is_average(self):
        """测试综合分数是各维度平均"""
        text = "冲突。争吵。突然。愤怒。" * 5
        result = self.analyzer.analyze(text)
        
        expected = (result['conflict'] + result['suspense'] + 
                   result['emotion'] + result['rhythm']) / 4
        assert abs(result['overall'] - expected) < 0.01
    
    def test_empty_text(self):
        """测试空文本"""
        text = "   "  # 只有空白字符
        result = self.analyzer.analyze(text)
        
        assert result['conflict'] == 0.0
        assert result['suspense'] == 0.0
        assert result['emotion'] == 0.0
        assert result['rhythm'] == 0.0
        assert result['overall'] == 0.0
    
    def test_scores_are_normalized(self):
        """测试分数在0-1范围内"""
        text = "冲突" * 100 + "悬念" * 100 + "愤怒" * 100 + "短句。" * 100
        result = self.analyzer.analyze(text)
        
        assert 0 <= result['conflict'] <= 1
        assert 0 <= result['suspense'] <= 1
        assert 0 <= result['emotion'] <= 1
        assert 0 <= result['rhythm'] <= 1
        assert 0 <= result['overall'] <= 1
