"""Git operations used by the auto-uploader."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class FileChange:
    path: str
    status: str


def run_git(args: List[str], repo_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=False,
    )


def ensure_repo(repo_path: Path) -> bool:
    result = run_git(["rev-parse", "--is-inside-work-tree"], repo_path)
    return result.returncode == 0


def get_branch(repo_path: Path) -> str:
    result = run_git(["branch", "--show-current"], repo_path)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    fallback = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    if fallback.returncode == 0:
        return fallback.stdout.strip() or "main"
    return "main"


def get_status(repo_path: Path) -> List[FileChange]:
    result = run_git(["status", "--porcelain"], repo_path)
    changes: List[FileChange] = []
    if result.returncode != 0:
        return changes
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status_code = line[:2]
        file_path = line[3:].strip()
        changes.append(FileChange(path=file_path, status=status_code))
    return changes


def get_diff(repo_path: Path, max_chars: int) -> str:
    result = run_git(["diff"], repo_path)
    if result.returncode != 0:
        return ""
    diff_text = result.stdout
    if len(diff_text) > max_chars:
        return diff_text[:max_chars] + "\n...diff truncated..."
    return diff_text


def get_diff_stat(repo_path: Path) -> str:
    result = run_git(["diff", "--stat"], repo_path)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def stage_all(repo_path: Path) -> bool:
    result = run_git(["add", "-A"], repo_path)
    return result.returncode == 0


def commit(repo_path: Path, message: str) -> bool:
    result = run_git(["commit", "-m", message], repo_path)
    return result.returncode == 0


def push(repo_path: Path, branch: str) -> bool:
    result = run_git(["push", "origin", branch], repo_path)
    return result.returncode == 0


def pull(repo_path: Path, branch: str) -> bool:
    result = run_git(["pull", "origin", branch], repo_path)
    return result.returncode == 0
