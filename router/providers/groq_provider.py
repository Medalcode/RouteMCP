import os
import json
import requests

from .base import AIProvider, ProviderError


class GroqProvider(AIProvider):
    name = "groq"

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self._available = bool(self.api_key)

    def is_available(self) -> bool:
        return self._available

    def ask(self, model: str, prompt: str) -> str:
        if not self._available:
            raise ProviderError(self.name, "API key not configured")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Map short names to Groq model IDs
        model_map = {
            "llama-3.3-70b": "llama-3.3-70b-versatile",
            "llama-3.1-8b": "llama-3.1-8b-instant",
            "mixtral-8x7b": "mixtral-8x7b-32768",
        }
        actual_model = model_map.get(model, model)
        payload = {
            "model": actual_model,
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
