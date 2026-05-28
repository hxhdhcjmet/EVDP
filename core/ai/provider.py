"""OpenAI-compatible chat completion client."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json

import requests


@dataclass
class AIProviderConfig:
    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.2
    timeout: int = 60

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"


class OpenAICompatibleClient:
    """Minimal client for providers that support the OpenAI chat completions API."""

    def __init__(self, config: AIProviderConfig):
        self.config = config

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1600) -> str:
        if not self.config.api_key:
            raise ValueError("API Key 不能为空")
        if not self.config.model:
            raise ValueError("模型名称不能为空")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.config.chat_completions_url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=self.config.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"模型接口返回错误 {response.status_code}: {response.text[:800]}")

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"模型响应格式不符合预期: {data}") from exc

    def test_connection(self) -> str:
        return self.chat(
            [
                {"role": "system", "content": "You are a concise API health check assistant."},
                {"role": "user", "content": "Reply with OK."},
            ],
            max_tokens=16,
        )
