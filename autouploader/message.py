"""Commit message construction and AI payload helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from .git_ops import FileChange


@dataclass(frozen=True)
class ChangeSummary:
    added: int
    modified: int
    deleted: int
    renamed: int
    untracked: int

    @property
    def total(self) -> int:
        return self.added + self.modified + self.deleted + self.renamed + self.untracked


def summarize_changes(changes: List[FileChange]) -> ChangeSummary:
    added = modified = deleted = renamed = untracked = 0
    for change in changes:
        code = change.status
        if code.startswith("??"):
            untracked += 1
        elif "A" in code:
            added += 1
        elif "D" in code:
            deleted += 1
        elif "R" in code:
            renamed += 1
        else:
            modified += 1
    return ChangeSummary(
        added=added,
        modified=modified,
        deleted=deleted,
        renamed=renamed,
        untracked=untracked,
    )


def format_summary(summary: ChangeSummary) -> str:
    return (
        f"{summary.added} added, {summary.modified} modified, {summary.deleted} deleted, "
        f"{summary.renamed} renamed, {summary.untracked} untracked"
    )


def build_rules_message(
    summary: ChangeSummary, template: str, timestamp: datetime
) -> str:
    summary_text = format_summary(summary)
    return template.format(summary=summary_text, timestamp=timestamp.isoformat())


def build_ai_payload(
    repo_path: str,
    branch: str,
    changes: List[FileChange],
    diff_stat: str,
    diff: str,
    default_message: str,
) -> Dict[str, object]:
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "repo_path": repo_path,
        "branch": branch,
        "timestamp": timestamp,
        "summary": format_summary(summarize_changes(changes)),
        "changes": [{"path": c.path, "status": c.status} for c in changes],
        "diff_stat": diff_stat,
        "diff": diff,
        "default_message": default_message,
    }
