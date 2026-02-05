"""Provider interface for commit message generation."""

from __future__ import annotations

from typing import Dict, Protocol


class CommitMessageProvider(Protocol):
    def generate_message(self, payload: Dict[str, object]) -> str: ...
