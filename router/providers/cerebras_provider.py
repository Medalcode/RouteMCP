import os
import json
import requests

from .base import AIProvider, ProviderError


class CerebrasProvider(AIProvider):
    name = "cerebras"

    def __init__(self):
        self.api_key = os.environ.get("CEREBRAS_API_KEY", "")
        self._available = bool(self.api_key)

    def is_available(self) -> bool:
        return self._available

    def ask(self, model: str, prompt: str) -> str:
        if not self._available:
            raise ProviderError(self.name, "API key not configured")
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama3.3-70b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 8192,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ProviderError(self.name, f"Unexpected response: {json.dumps(data, indent=2)[:300]}")
