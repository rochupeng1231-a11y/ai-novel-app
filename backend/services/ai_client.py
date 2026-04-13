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

    async def stream_generate(self, prompt: str, **kwargs):
        """流式调用Kimi API"""
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not set")

        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip() or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        import json
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content

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

    async def stream_generate(self, prompt: str, **kwargs):
        """流式调用DeepSeek API"""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")

        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip() or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        import json
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content

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

    async def stream_generate(self, prompt: str, **kwargs):
        """流式调用MiniMax API"""
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048),
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip() or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        import json
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content

    def get_model_name(self) -> str:
        return f"MiniMax/{self.model}"


class MiniMaxAnthropicClient(AIBaseClient):
    """MiniMax API - Anthropic兼容格式（Claude Code 用的同一接口）"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimaxi.com/anthropic/v1"
        self.model = "MiniMax-M2.7"

    async def generate(self, prompt: str, **kwargs) -> str:
        """调用MiniMax API（Anthropic兼容格式）"""
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 2048),
                    "temperature": kwargs.get("temperature", 0.7)
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def stream_generate(self, prompt: str, **kwargs):
        """流式调用MiniMax API（Anthropic兼容格式，SSE）"""
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": kwargs.get("max_tokens", 2048),
                        "temperature": kwargs.get("temperature", 0.7),
                        "stream": True
                    }
                ) as response:
                    # HTTP 状态码非 200 直接抛出（不用读取 body）
                    if response.status_code != 200:
                        raise Exception(f"HTTP {response.status_code}")

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            import json
                            try:
                                data = json.loads(data_str)
                                # Anthropic SSE 格式：{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"xxx"}}
                                if data.get("type") == "error":
                                    # SSE 数据里的 error，也要抛出触发 fallback
                                    err_msg = data.get("error", {}).get("message", "unknown error")
                                    raise Exception(f"SSE error: {err_msg}")
                                elif data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue
        except httpx.ReadTimeout:
            raise Exception("ReadTimeout: MiniMax 服务响应超时")
        except httpx.HTTPError as e:
            # httpx 的 HTTP 错误（如 529），包装后抛出
            raise Exception(f"HTTP error: {e}")

    def get_model_name(self) -> str:
        return f"MiniMax-Anthropic/{self.model}"


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
            "minimax_anthropic": MiniMaxAnthropicClient(),
        }
        # 流式生成的降级顺序（DeepSeek 最稳定放最前）
        self.stream_fallback = ["deepseek", "minimax_anthropic", "minimax", "kimi", "claude"]

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

    async def stream_generate(self, task_type: str, prompt: str, **kwargs):
        """流式生成文本，按 fallback 顺序自动降级"""
        tried = set()

        while True:
            # 按 fallback 顺序选择未试过的 client
            client_name = None
            for name in self.stream_fallback:
                if name not in tried and self.clients[name].api_key:
                    client_name = name
                    break

            if not client_name:
                raise RuntimeError("所有 AI provider 都不可用或未配置")

            tried.add(client_name)
            client = self.clients[client_name]

            try:
                print(f"[AI] 使用 provider: {client_name}")
                async for chunk in client.stream_generate(prompt, **kwargs):
                    yield chunk, client.get_model_name()
                return  # 成功完成
            except Exception as e:
                error_msg = str(e)
                # 判断是否限流/过载错误，触发 fallback
                is_rate_limit = any(kw in error_msg.lower() for kw in [
                    "529", "overloaded", "rate_limit", "rate limit",
                    "readtimeout", "timeout", "service unavailable",
                    "overloaded_error", "request rate surge",
                    "服务集群负载较高", "服务繁忙", "服务器负载"
                ])
                if is_rate_limit:
                    print(f"[AI] {client_name} 限流/超时: {error_msg[:100]}，切换到下一个 provider...")
                    continue  # 尝试下一个 provider
                else:
                    raise  # 其他错误直接抛出


# 全局单例
ai_aggregator = AIAggregator()
