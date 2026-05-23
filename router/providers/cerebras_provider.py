import asyncio
import json
import logging
import os

import httpx

from .base import AIProvider, ProviderError

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [1, 2, 4]
_MAX_RETRIES = 3


class CerebrasProvider(AIProvider):
    name = "cerebras"

    def __init__(self):
        self.api_key = os.environ.get("CEREBRAS_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        self._base_url = "https://api.cerebras.ai/v1"

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = await self._client.get(f"{self._base_url}/models", headers=headers)
            return resp.status_code == 200
        except Exception:
            logger.exception("%s availability check failed", self.name)
            return False

    async def ask(self, model: str, prompt: str) -> str:
        if not self.api_key:
            raise ProviderError(self.name, "API key not configured")
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
        last_error = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning("%s | attempt %d/%d network error: %s", self.name, attempt + 1, _MAX_RETRIES, e)
                last_error = ProviderError(self.name, f"Network error: {e}")
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                continue
            if resp.status_code in (429,) or resp.status_code >= 500:
                logger.warning("%s | attempt %d/%d HTTP %d", self.name, attempt + 1, _MAX_RETRIES, resp.status_code)
                last_error = ProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                continue
            if resp.status_code != 200:
                raise ProviderError(self.name, f"HTTP {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise ProviderError(self.name, f"Unexpected response: {json.dumps(data, indent=2)[:300]}")
        raise last_error
