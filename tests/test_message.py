"""Tests for commit message utilities."""

from datetime import datetime, timezone

from autouploader.git_ops import FileChange
from autouploader.message import build_rules_message, summarize_changes


def test_summarize_changes() -> None:
    changes = [
        FileChange(path="a.txt", status="A "),
        FileChange(path="b.txt", status=" M"),
        FileChange(path="c.txt", status="D "),
        FileChange(path="d.txt", status="??"),
    ]
    summary = summarize_changes(changes)
    assert summary.added == 1
    assert summary.modified == 1
    assert summary.deleted == 1
    assert summary.untracked == 1


def test_build_rules_message() -> None:
    changes = [FileChange(path="a.txt", status="A ")]
    summary = summarize_changes(changes)
    ts = datetime(2026, 2, 5, tzinfo=timezone.utc)
    message = build_rules_message(summary, "auto: {summary} [{timestamp}]", ts)
    assert "auto:" in message
    assert "added" in message
