"""Local HTTP provider for commit message generation."""

from __future__ import annotations

import json
import urllib.request
from typing import Dict

from .base import CommitMessageProvider


class LocalHttpProvider(CommitMessageProvider):
    def __init__(
        self, endpoint: str, timeout_seconds: int, headers: Dict[str, str]
    ) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.headers = {"Content-Type": "application/json", **headers}

    def generate_message(self, payload: Dict[str, object]) -> str:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint, data=data, headers=self.headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        response_data = json.loads(body)
        message = response_data.get("message", "").strip()
        return message
