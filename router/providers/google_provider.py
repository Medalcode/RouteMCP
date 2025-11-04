import os
from typing import Optional
import requests
import json

from .base import AIProvider, ProviderError


class GoogleProvider(AIProvider):
    name = "google"

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self._available = bool(self.api_key)

    def is_available(self) -> bool:
        return self._available

    def ask(self, model: str, prompt: str) -> str:
        if not self._available:
            raise ProviderError(self.name, "API key not configured")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
            },
        }
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ProviderError(self.name, f"Unexpected response: {json.dumps(data, indent=2)[:300]}")
