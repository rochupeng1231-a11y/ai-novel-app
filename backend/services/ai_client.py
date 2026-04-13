"""
AI 客户端 - 统一接口对接多个AI服务
"""
import os
import httpx
from typing import Optional
from abc import ABC, abstractmethod


class AIBaseClient(ABC):
    """AI客户端基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
        pass


class KimiClient(AIBaseClient):
    """Kimi API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.moonshot.cn/v1"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url
        self.model = "moonshot-v1-8k"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用Kimi API"""
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_model_name(self) -> str:
        return f"Kimi/{self.model}"


class DeepSeekClient(AIBaseClient):
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.model = "deepseek-chat"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_model_name(self) -> str:
        return f"DeepSeek/{self.model}"


class ClaudeClient(AIBaseClient):
    """Claude API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.base_url = base_url
        self.model = "claude-3-haiku-20240307"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用Claude API"""
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 1024),
                    "temperature": kwargs.get("temperature", 0.7)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    def get_model_name(self) -> str:
        return f"Claude/{self.model}"


class MiniMaxClient(AIBaseClient):
    """MiniMax API 客户端 (与OpenClaw一致)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimaxi.com/v1"
        self.model = "MiniMax-M2.7"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """调用MiniMax API (OpenAI Completions兼容格式)"""
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 4096)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_model_name(self) -> str:
        return f"MiniMax/{self.model}"


class AIAggregator:
    """AI聚合器 - 根据任务类型选择合适的AI"""
    
    # 模型分层策略
    MODEL_STRATEGY = {
        "outline": "deepseek",      # 大纲构思 → DeepSeek（性价比高）
        "draft": "kimi",             # 草稿生成 → Kimi（中文好，长上下文）
        "core": "claude",           # 核心章节 → Claude（文字质量最高）
        "polish": "claude",         # 润色精修 → Claude
        "minimax": "minimax",       # MiniMax（你的密钥）
    }
    
    def __init__(self):
        self.clients = {
            "kimi": KimiClient(),
            "deepseek": DeepSeekClient(),
            "claude": ClaudeClient(),
            "minimax": MiniMaxClient(),
        }
    
    def get_client(self, task_type: str) -> AIBaseClient:
        """根据任务类型获取AI客户端"""
        provider = self.MODEL_STRATEGY.get(task_type, "deepseek")
        return self.clients[provider]
    
    async def generate(self, task_type: str, prompt: str, **kwargs) -> tuple[str, str]:
        """
        生成文本
        返回: (生成的文本, 使用的模型名)
        """
        client = self.get_client(task_type)
        result = await client.generate(prompt, **kwargs)
        return result, client.get_model_name()


# 全局单例
ai_aggregator = AIAggregator()
