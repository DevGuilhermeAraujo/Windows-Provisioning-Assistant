from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TaskBase(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        required_fields: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.required_fields = required_fields or []

    def validate_context(self, context: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        for field in self.required_fields:
            value = context.get(field)
            if value is None:
                missing.append(field)
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(field)
        return missing

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
