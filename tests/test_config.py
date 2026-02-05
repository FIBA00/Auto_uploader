"""Tests for configuration load/save."""

import json
import tempfile
from pathlib import Path

from autouploader.config import Config, load_config, save_config


def test_config_roundtrip() -> None:
    config = Config(repo_path="/tmp/repo", poll_seconds=10, use_ai=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "config.json"
        saved_path = save_config(config, path)
        assert saved_path == path
        loaded = load_config(path)
        assert loaded.repo_path == config.repo_path
        assert loaded.poll_seconds == config.poll_seconds
        assert loaded.use_ai == config.use_ai


def test_config_serializes() -> None:
    config = Config(repo_path="/tmp/repo")
    data = json.dumps(config.to_dict())
    assert "repo_path" in data
