"""Provider registry and factory."""

from __future__ import annotations

from typing import Dict

from .base import CommitMessageProvider
from .local_http import LocalHttpProvider


def get_provider(name: str, settings: Dict[str, object]) -> CommitMessageProvider:
    if name == "local_http":
        endpoint = str(settings.get("ai_endpoint", "http://localhost:8080/commit"))
        timeout_seconds = int(settings.get("ai_timeout_seconds", 15))
        headers = dict(settings.get("ai_extra_headers", {}))
        return LocalHttpProvider(endpoint, timeout_seconds, headers)
    raise ValueError(f"Unknown AI provider: {name}")
