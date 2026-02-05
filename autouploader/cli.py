"""CLI entrypoint for the auto-uploader daemon."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from .config import Config, get_log_path, get_pid_path, load_config, save_config
from .engine import AutoCommitEngine

_SHOULD_EXIT = False


def _set_exit_flag(_signum: int, _frame: object) -> None:
    global _SHOULD_EXIT
    _SHOULD_EXIT = True


def _get_executable() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def _pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _write_pid(pid_path: Path, pid: int) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(pid), encoding="utf-8")


def _read_pid(pid_path: Path) -> Optional[int]:
    if not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _clear_pid(pid_path: Path) -> None:
    if pid_path.exists():
        pid_path.unlink()


def run_loop(config: Config, repo_path: Optional[str]) -> int:
    signal.signal(signal.SIGTERM, _set_exit_flag)
    signal.signal(signal.SIGINT, _set_exit_flag)

    engine = AutoCommitEngine(config, repo_path)

    while not _SHOULD_EXIT:
        result = engine.run_once()
        if result.details != "No changes detected":
            print(result.details)
        time.sleep(config.poll_seconds)

    return 0


def start_daemon(config: Config, repo_path: Optional[str]) -> int:
    pid_path = get_pid_path()
    existing = _read_pid(pid_path)
    if existing and _pid_running(existing):
        print(f"Already running with PID {existing}")
        return 0

    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_path, "a", encoding="utf-8")

    args = [
        _get_executable(),
        "-m",
        "autouploader",
        "run",
    ]
    if repo_path:
        args += ["--repo", repo_path]

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    process = subprocess.Popen(
        args,
        stdout=log_handle,
        stderr=log_handle,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    _write_pid(pid_path, process.pid)
    print(f"Started daemon with PID {process.pid}")
    return 0


def stop_daemon() -> int:
    pid_path = get_pid_path()
    pid = _read_pid(pid_path)
    if not pid:
        print("No running daemon found")
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
        _clear_pid(pid_path)
        print(f"Stopped daemon with PID {pid}")
        return 0
    except OSError as exc:
        print(f"Failed to stop daemon: {exc}")
        return 1


def status_daemon() -> int:
    pid = _read_pid(get_pid_path())
    if pid and _pid_running(pid):
        print(f"Running (PID {pid})")
        return 0
    print("Not running")
    return 1


def init_config(path: Optional[str]) -> int:
    config = Config()
    target = Path(path).expanduser().resolve() if path else None
    saved = save_config(config, target)
    print(f"Config written to {saved}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-commit daemon")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start daemon")
    start_parser.add_argument("--repo", help="Repository path")

    subparsers.add_parser("stop", help="Stop daemon")
    subparsers.add_parser("status", help="Check daemon status")

    run_parser = subparsers.add_parser("run", help="Run daemon loop")
    run_parser.add_argument("--repo", help="Repository path")

    once_parser = subparsers.add_parser("run-once", help="Run once and exit")
    once_parser.add_argument("--repo", help="Repository path")

    config_parser = subparsers.add_parser("config", help="Write default config")
    config_parser.add_argument("--path", help="Optional config path")

    args = parser.parse_args()
    config = load_config()

    if args.command == "start":
        raise SystemExit(start_daemon(config, args.repo))
    if args.command == "stop":
        raise SystemExit(stop_daemon())
    if args.command == "status":
        raise SystemExit(status_daemon())
    if args.command == "run":
        raise SystemExit(run_loop(config, args.repo))
    if args.command == "run-once":
        engine = AutoCommitEngine(config, args.repo)
        result = engine.run_once()
        print(result.details)
        raise SystemExit(0 if result.committed else 1)
    if args.command == "config":
        raise SystemExit(init_config(args.path))


if __name__ == "__main__":
    main()
