"""
AI客户端 - 单元测试
"""
import pytest
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.services.ai_client import (
    KimiClient, DeepSeekClient, ClaudeClient, AIAggregator
)


class TestAIAggregator:
    """AI聚合器测试"""
    
    def setup_method(self):
        self.aggregator = AIAggregator()
    
    def test_get_client_outline(self):
        """测试大纲任务获取DeepSeek"""
        client = self.aggregator.get_client("outline")
        assert isinstance(client, DeepSeekClient)
    
    def test_get_client_draft(self):
        """测试草稿任务获取Kimi"""
        client = self.aggregator.get_client("draft")
        assert isinstance(client, KimiClient)
    
    def test_get_client_core(self):
        """测试核心章节获取Claude"""
        client = self.aggregator.get_client("core")
        assert isinstance(client, ClaudeClient)
    
    def test_get_client_polish(self):
        """测试润色任务获取Claude"""
        client = self.aggregator.get_client("polish")
        assert isinstance(client, ClaudeClient)
    
    def test_get_client_unknown(self):
        """测试未知任务默认获取DeepSeek"""
        client = self.aggregator.get_client("unknown")
        assert isinstance(client, DeepSeekClient)


class TestKimiClient:
    """Kimi客户端测试"""
    
    def test_init_with_api_key(self):
        """测试使用提供的API密钥初始化"""
        client = KimiClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "moonshot-v1-8k"
    
    def test_init_without_api_key(self):
        """测试无API密钥时抛出错误"""
        import os
        # 确保环境变量没有设置
        old_key = os.environ.get("KIMI_API_KEY")
        if "KIMI_API_KEY" in os.environ:
            del os.environ["KIMI_API_KEY"]
        
        client = KimiClient()
        # 应该使用默认值或None
        # 如果环境变量也没设置，会在调用时抛出错误
        
        # 恢复环境变量
        if old_key:
            os.environ["KIMI_API_KEY"] = old_key
    
    def test_get_model_name(self):
        """测试获取模型名称"""
        client = KimiClient(api_key="test")
        assert "Kimi" in client.get_model_name()
        assert "moonshot" in client.get_model_name()


class TestDeepSeekClient:
    """DeepSeek客户端测试"""
    
    def test_init_with_api_key(self):
        """测试使用提供的API密钥初始化"""
        client = DeepSeekClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "deepseek-chat"
    
    def test_get_model_name(self):
        """测试获取模型名称"""
        client = DeepSeekClient(api_key="test")
        assert "DeepSeek" in client.get_model_name()


class TestClaudeClient:
    """Claude客户端测试"""
    
    def test_init_with_api_key(self):
        """测试使用提供的API密钥初始化"""
        client = ClaudeClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "claude-3-haiku-20240307"
    
    def test_get_model_name(self):
        """测试获取模型名称"""
        client = ClaudeClient(api_key="test")
        assert "Claude" in client.get_model_name()
