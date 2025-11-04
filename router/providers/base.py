from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def ask(self, model: str, prompt: str) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class ProviderError(Exception):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider}] {message}")
