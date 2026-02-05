"""Core auto-commit engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fnmatch
from pathlib import Path
from typing import List, Optional

from .config import Config
from .git_ops import (
    commit,
    ensure_repo,
    get_branch,
    get_diff,
    get_diff_stat,
    get_status,
    FileChange,
    pull,
    push,
    stage_all,
)
from .message import build_ai_payload, build_rules_message, summarize_changes
from .providers.registry import get_provider


@dataclass(frozen=True)
class RunResult:
    committed: bool
    message: str
    details: str


class AutoCommitEngine:
    def __init__(self, config: Config, repo_path: Optional[str] = None) -> None:
        self.config = config
        self.repo_path = Path(repo_path or config.repo_path).expanduser().resolve()

    def _filter_changes(self, changes: List[FileChange]) -> List[FileChange]:
        if not self.config.include_patterns and not self.config.ignore_patterns:
            return changes

        filtered = []
        for change in changes:
            path = change.path
            if self.config.include_patterns:
                if not any(
                    fnmatch.fnmatch(path, pattern)
                    for pattern in self.config.include_patterns
                ):
                    continue
            if self.config.ignore_patterns:
                if any(
                    fnmatch.fnmatch(path, pattern)
                    for pattern in self.config.ignore_patterns
                ):
                    continue
            filtered.append(change)
        return filtered

    def run_once(self) -> RunResult:
        if not self.repo_path.exists():
            return RunResult(False, "", f"Repo path not found: {self.repo_path}")
        if not ensure_repo(self.repo_path):
            return RunResult(False, "", "Not a git repository")

        changes = self._filter_changes(get_status(self.repo_path))
        if not changes:
            return RunResult(False, "", "No changes detected")

        summary = summarize_changes(changes)
        timestamp = datetime.now(timezone.utc)
        default_message = build_rules_message(
            summary, self.config.commit_message_template, timestamp
        )
        commit_message = default_message

        ai_warning = ""
        if self.config.use_ai:
            try:
                payload = build_ai_payload(
                    str(self.repo_path),
                    get_branch(self.repo_path),
                    changes,
                    get_diff_stat(self.repo_path),
                    get_diff(self.repo_path, self.config.max_diff_chars),
                    default_message,
                )
                provider = get_provider(self.config.ai_provider, self.config.to_dict())
                ai_message = provider.generate_message(payload).strip()
                if ai_message:
                    commit_message = ai_message
            except Exception as exc:
                ai_warning = f"AI provider failed, using default message: {exc}"

        if not stage_all(self.repo_path):
            return RunResult(False, "", "Failed to stage changes")

        if not commit(self.repo_path, commit_message):
            return RunResult(False, commit_message, "Commit failed")

        if self.config.push_after_commit:
            branch = get_branch(self.repo_path)
            pull(self.repo_path, branch)
            if not push(self.repo_path, branch):
                details = "Commit ok, push failed"
                if ai_warning:
                    details = f"{details}. {ai_warning}"
                return RunResult(True, commit_message, details)

        details = "Commit and push completed"
        if ai_warning:
            details = f"{details}. {ai_warning}"
        return RunResult(True, commit_message, details)
