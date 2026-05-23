from typing import Optional

from router.models import MODELS, TASK_ROUTING, ModelInfo
from router.classifier import classify
from router.providers.google_provider import GoogleProvider
from router.providers.groq_provider import GroqProvider
from router.providers.cerebras_provider import CerebrasProvider
from router.providers.base import ProviderError


class RouterEngine:
    def __init__(self):
        self.providers = {
            "google": GoogleProvider(),
            "groq": GroqProvider(),
            "cerebras": CerebrasProvider(),
        }

    async def get_available_models(self) -> list[ModelInfo]:
        available = []
        for m in MODELS:
            prov = self.providers.get(m.provider)
            if prov and await prov.is_available():
                available.append(m)
        return available

    async def route(self, prompt: str, task_type: Optional[str] = None) -> str:
        task = classify(prompt, task_type)
        preferences = TASK_ROUTING.get(task, TASK_ROUTING["general"])
        errors = []
        for model_id in preferences:
            model = next((m for m in MODELS if m.id == model_id), None)
            if not model:
                continue
            prov = self.providers.get(model.provider)
            if not prov or not await prov.is_available():
                continue
            try:
                result = await prov.ask(model_id, prompt)
                return result
            except ProviderError as e:
                errors.append(str(e))
                continue
        raise ProviderError("router", f"No models available. Errors: {'; '.join(errors) if errors else 'all providers unavailable'}")

    async def ask(self, model_id: str, prompt: str) -> str:
        model = next((m for m in MODELS if m.id == model_id), None)
        if not model:
            raise ProviderError("router", f"Unknown model: {model_id}")
        prov = self.providers.get(model.provider)
        if not prov:
            raise ProviderError("router", f"Unknown provider: {model.provider}")
        if not await prov.is_available():
            raise ProviderError(model.provider, "Provider not available (API key missing)")
        return await prov.ask(model_id, prompt)

    async def compare(self, prompt: str, model_ids: list[str]) -> dict[str, str]:
        results = {}
        for model_id in model_ids:
            try:
                results[model_id] = await self.ask(model_id, prompt)
            except ProviderError as e:
                results[model_id] = f"ERROR: {e}"
        return results
