"""
AI 客户端 - 使用 Anthropic SDK 进行 MiniMax 流式交互
"""
import anthropic

from backend.config import (
    MAX_TOKENS, TIMEOUT, TEMPERATURE, MINIMAX_API_KEY, MINIMAX_ANTHROPIC_BASE_URL, MINIMAX_MODEL
)


class MiniMaxAnthropicClient:
    """MiniMax API - 使用官方 AsyncAnthropic SDK"""

    def __init__(self):
        self.api_key = MINIMAX_API_KEY
        self.base_url = MINIMAX_ANTHROPIC_BASE_URL
        self.model = MINIMAX_MODEL
        self._client = None

    def get_model_name(self) -> str:
        return f"MiniMax/{self.model}"

    def _get_client(self) -> anthropic.AsyncAnthropic:
        """获取或创建 AsyncAnthropic 客户端"""
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=anthropic.Timeout(TIMEOUT)
            )
        return self._client

    async def generate(self, prompt: str, **kwargs) -> str:
        """非流式生成文本"""
        if not self.api_key:
            raise ValueError("MiniMax API key not set")

        client = self._get_client()
        response = await client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", MAX_TOKENS),
            temperature=kwargs.get("temperature", TEMPERATURE),
            messages=[{"role": "user", "content": prompt}]
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本 - 使用 AsyncAnthropic SDK

        Args:
            prompt: 用户输入的提示词
            **kwargs: max_tokens, temperature

        Yields:
            str: 文本块
        """
        if not self.api_key:
            raise ValueError("MiniMax API key not set")

        client = self._get_client()
        max_tokens = kwargs.get("max_tokens", MAX_TOKENS)
        temperature = kwargs.get("temperature", TEMPERATURE)

        try:
            async with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        delta = getattr(event, "delta", None)
                        if delta and delta.type == "text_delta":
                            yield delta.text
                    elif event.type == "error":
                        error_obj = getattr(event, "error", None)
                        if error_obj:
                            raise Exception(f"API Error: {error_obj}")
        except Exception as e:
            print(f"[MiniMax] Stream error: {e}")
            raise


# 单例实例
mini_max_client = MiniMaxAnthropicClient()


async def stream_generate(prompt: str, **kwargs):
    """流式生成文本的便捷函数

    Args:
        prompt: 用户输入的提示词
        **kwargs: max_tokens, temperature

    Yields:
        str: 文本块
    """
    async for chunk in mini_max_client.stream_generate(prompt, **kwargs):
        yield chunk