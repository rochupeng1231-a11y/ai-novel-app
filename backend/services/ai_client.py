"""
AI 客户端 - 统一接口对接多个AI服务
"""
import json
from typing import Optional
from abc import ABC, abstractmethod

import httpx

from backend.config import (
    MAX_TOKENS, TIMEOUT, TEMPERATURE,
    MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL, MINIMAX_ANTHROPIC_BASE_URL,
    KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    CLAUDE_API_KEY, CLAUDE_BASE_URL, CLAUDE_MODEL,
    MODEL_STRATEGY, STREAM_FALLBACK, RATE_LIMIT_KEYWORDS
)


class AIBaseClient(ABC):
    """AI客户端基类"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
        pass

    def _get_headers(self) -> dict:
        """获取请求头 - 子类可覆盖"""
        return {"Authorization": f"Bearer {self.api_key}"}

    def _get_json_body(self, prompt: str, **kwargs) -> dict:
        """获取请求体 - 子类可覆盖"""
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", MAX_TOKENS)
        }

    def _get_endpoint(self, endpoint_type: str) -> str:
        """获取端点 - 子类覆盖"""
        return f"{self.base_url}/chat/completions"

    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本 - OpenAI兼容格式"""
        if not self.api_key:
            raise ValueError(f"{self.__class__.__name__} API key not set")

        headers = self._get_headers()
        json_body = self._get_json_body(prompt, **kwargs)

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                self._get_endpoint("generate"),
                headers=headers,
                json=json_body
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)

    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本 - OpenAI兼容格式"""
        if not self.api_key:
            raise ValueError(f"{self.__class__.__name__} API key not set")

        headers = self._get_headers()
        json_body = self._get_json_body(prompt, **kwargs)
        json_body["stream"] = True

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream(
                "POST",
                self._get_endpoint("stream"),
                headers=headers,
                json=json_body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = self._parse_stream_data(data)
                            if content:
                                yield content
                        except Exception as e:
                            print(f"[AI Client] Stream parse error: {e}")
                            continue

    def _parse_response(self, data: dict) -> str:
        """解析响应 - OpenAI格式"""
        return data["choices"][0]["message"]["content"]

    def _parse_stream_data(self, data: dict) -> str:
        """解析流式数据 - OpenAI格式"""
        try:
            choices = data.get("choices")
            if not choices or not choices[0]:
                return ""
            delta = choices[0].get("delta", {})
            return delta.get("content", "") or ""
        except (IndexError, TypeError, AttributeError):
            return ""


class OpenAICompatibleClient(AIBaseClient):
    """OpenAI兼容格式的AI客户端基类"""

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__(api_key)
        self.base_url = base_url
        self.model = model


class KimiClient(OpenAICompatibleClient):
    """Kimi API 客户端"""

    def __init__(self):
        super().__init__(KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL)

    def get_model_name(self) -> str:
        return f"Kimi/{self.model}"


class DeepSeekClient(OpenAICompatibleClient):
    """DeepSeek API 客户端"""

    MAX_TOKENS_LIMIT = 8192  # DeepSeek限制

    def __init__(self):
        super().__init__(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL)

    def get_model_name(self) -> str:
        return f"DeepSeek/{self.model}"

    def _get_json_body(self, prompt: str, **kwargs) -> dict:
        """DeepSeek的max_tokens上限是8192"""
        body = super()._get_json_body(prompt, **kwargs)
        if body.get("max_tokens", 0) > self.MAX_TOKENS_LIMIT:
            body["max_tokens"] = self.MAX_TOKENS_LIMIT
        return body


class MiniMaxClient(OpenAICompatibleClient):
    """MiniMax API 客户端 (OpenAI兼容格式)"""

    def __init__(self):
        super().__init__(MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL)

    def get_model_name(self) -> str:
        return f"MiniMax/{self.model}"

    def _get_endpoint(self, endpoint_type: str) -> str:
        """MiniMax 使用不同的端点路径"""
        return f"{self.base_url}/text/chatcompletion_v2"


class ClaudeClient(AIBaseClient):
    """Claude API 客户端"""

    def __init__(self):
        super().__init__(CLAUDE_API_KEY)
        self.base_url = CLAUDE_BASE_URL
        self.model = CLAUDE_MODEL

    def get_model_name(self) -> str:
        return f"Claude/{self.model}"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    def _get_endpoint(self, endpoint_type: str) -> str:
        return f"{self.base_url}/v1/messages"

    def _parse_response(self, data: dict) -> str:
        return data["content"][0]["text"]


class MiniMaxAnthropicClient(AIBaseClient):
    """MiniMax API - Anthropic兼容格式"""

    def __init__(self):
        super().__init__(MINIMAX_API_KEY)
        self.base_url = MINIMAX_ANTHROPIC_BASE_URL
        self.model = MINIMAX_MODEL

    def get_model_name(self) -> str:
        return f"MiniMax-Anthropic/{self.model}"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    def _get_endpoint(self, endpoint_type: str) -> str:
        return f"{self.base_url}/messages"

    def _parse_stream_data(self, data: dict) -> str:
        """解析流式数据 - Anthropic格式"""
        if data.get("type") == "error":
            err_msg = data.get("error", {}).get("message", "unknown error")
            raise Exception(f"SSE error: {err_msg}")
        elif data.get("type") == "content_block_delta":
            delta = data.get("delta", {})
            # 处理 text_delta 和 thinking_delta
            if delta.get("type") == "text_delta":
                return delta.get("text", "")
            elif delta.get("type") == "thinking_delta":
                return ""  # 忽略思考过程
        return ""


class AIAggregator:
    """AI聚合器 - 根据任务类型选择合适的AI"""

    def __init__(self):
        self.clients = {
            "kimi": KimiClient(),
            "deepseek": DeepSeekClient(),
            "claude": ClaudeClient(),
            "minimax": MiniMaxClient(),
            "minimax_anthropic": MiniMaxAnthropicClient(),
        }

    def get_client(self, task_type: str) -> AIBaseClient:
        """根据任务类型获取AI客户端"""
        provider = MODEL_STRATEGY.get(task_type, "deepseek")
        return self.clients[provider]

    async def generate(self, task_type: str, prompt: str, **kwargs) -> tuple[str, str]:
        """生成文本"""
        client = self.get_client(task_type)
        result = await client.generate(prompt, **kwargs)
        return result, client.get_model_name()

    async def stream_generate(self, task_type: str, prompt: str, **kwargs):
        """流式生成文本，按 fallback 顺序自动降级"""
        tried = set()

        while True:
            client_name = None
            for name in STREAM_FALLBACK:
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
                return
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = any(kw in error_msg.lower() for kw in RATE_LIMIT_KEYWORDS)
                if is_rate_limit:
                    print(f"[AI] {client_name} 限流/超时: {error_msg[:100]}，切换到下一个 provider...")
                    continue
                else:
                    raise


ai_aggregator = AIAggregator()
