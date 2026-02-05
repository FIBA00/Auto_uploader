"""Configuration management for the auto-uploader."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CONFIG_DIR_NAME = ".autouploader"
DEFAULT_CONFIG_FILE_NAME = "config.json"
DEFAULT_LOG_FILE_NAME = "autouploader.log"
DEFAULT_PID_FILE_NAME = "autouploader.pid"


def get_config_dir() -> Path:
    env_dir = os.getenv("AUTOUPLOADER_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path.home() / DEFAULT_CONFIG_DIR_NAME


def get_config_path() -> Path:
    env_path = os.getenv("AUTOUPLOADER_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return get_config_dir() / DEFAULT_CONFIG_FILE_NAME


def get_log_path() -> Path:
    return get_config_dir() / DEFAULT_LOG_FILE_NAME


def get_pid_path() -> Path:
    return get_config_dir() / DEFAULT_PID_FILE_NAME


@dataclass
class Config:
    repo_path: str = ""
    poll_seconds: int = 120
    use_ai: bool = False
    ai_provider: str = "local_http"
    ai_endpoint: str = "http://localhost:8080/commit"
    ai_timeout_seconds: int = 15
    ai_extra_headers: Dict[str, str] = field(default_factory=dict)
    commit_message_template: str = "auto: {summary} [{timestamp}]"
    push_after_commit: bool = True
    include_patterns: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=list)
    max_diff_chars: int = 8000

    def to_dict(self) -> Dict[str, object]:
        return {
            "repo_path": self.repo_path,
            "poll_seconds": self.poll_seconds,
            "use_ai": self.use_ai,
            "ai_provider": self.ai_provider,
            "ai_endpoint": self.ai_endpoint,
            "ai_timeout_seconds": self.ai_timeout_seconds,
            "ai_extra_headers": self.ai_extra_headers,
            "commit_message_template": self.commit_message_template,
            "push_after_commit": self.push_after_commit,
            "include_patterns": self.include_patterns,
            "ignore_patterns": self.ignore_patterns,
            "max_diff_chars": self.max_diff_chars,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Config":
        return cls(
            repo_path=str(data.get("repo_path", "")),
            poll_seconds=int(data.get("poll_seconds", 120)),
            use_ai=bool(data.get("use_ai", False)),
            ai_provider=str(data.get("ai_provider", "local_http")),
            ai_endpoint=str(data.get("ai_endpoint", "http://localhost:8080/commit")),
            ai_timeout_seconds=int(data.get("ai_timeout_seconds", 15)),
            ai_extra_headers=dict(data.get("ai_extra_headers", {})),
            commit_message_template=str(
                data.get("commit_message_template", "auto: {summary} [{timestamp}]")
            ),
            push_after_commit=bool(data.get("push_after_commit", True)),
            include_patterns=list(data.get("include_patterns", [])),
            ignore_patterns=list(data.get("ignore_patterns", [])),
            max_diff_chars=int(data.get("max_diff_chars", 8000)),
        )


def load_config(path: Optional[Path] = None) -> Config:
    config_path = path or get_config_path()
    if not config_path.exists():
        return Config()
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return Config.from_dict(data)


def save_config(config: Config, path: Optional[Path] = None) -> Path:
    config_path = path or get_config_path()
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, indent=2, sort_keys=True)
    return config_path
