# config/settings.py 
# DataForgeConfig is the central configuration dataclass for all tools.
# All directory/file paths are initialized using DirManager at startup.
# All tools should receive a reference to this config and use only the parts they need.

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Set


def get_project_root():
    """Return the project root directory, compatible with PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class UserConfig:
    """Configuration for GitHub user with multiple repositories.

    Note:
        Both 'username' and 'token' are required arguments.
        Even if you want an empty value, you must explicitly pass something
        (e.g., an empty string '') when constructing this dataclass.
        This is necessary because there are no default values for these fields.
    """

    username: str = None  # required, must be provided (even if empty)
    token: str = None  # required, must be provided (even if empty)
    repos: List[str] = field(default_factory=list)  # optional, defaults to empty list

    # Suggestion: If you want to allow username/token to be optional,
    # you could set default values here, but that would change the logic.


@dataclass
class Settings:
    """
    Central configuration class for all tools in the system.
    All directory/file paths should be set at startup using DirManager.
    All other config fields (flags, tokens, etc.) are included here as well.
    Tools should only use this config, not DirManager directly.
    """
    settings_path = "settings.json"
    if not os.path.exists(settings_path):
        print("The settings json path doesnt exist using current values.")
        pass 
    else:
        with open(settings_path, "r") as f:
            settings_data = json.load(f)
            pass
    
    # TODO: Load the settings from json or use current setup if the file doesnt exist
     
    # Repository processing configuration
    max_repo_retries: int = 2
    max_retries: int = 3
    git_api_url: str = "https://api.github.com"
   
    # List of directories to ignore
    # NOTE: Use set literal in default_factory lambda for correct syntax and to avoid mutable default argument issues.
    ignore_dirs: Set[str] = field(
        default_factory=lambda: {
            ".git",
            ".github",
            ".vscode",
            "__pycache__",
            "node_modules",
            "venv",
            "env",
            ".idea",
            "dist",
            "build",
            "docs",
            "tests",
            "test",
            "cache",
            "temp",
            "tmp",
            "log",
            "logs",
        }
    )

    def __post_init__(self) -> None:
        project_root = get_project_root()
        files_dir = os.path.join(project_root, "Files")
        self._all_numbers_csv_path: str = os.path.abspath(
            os.path.join(files_dir, "AllNumber.csv")
        )
        self._pink_csv_path: str = os.path.abspath(
            os.path.join(files_dir, "PinkData.csv")
        )
        self._strategic_csv_path: str = os.path.abspath(
            os.path.join(files_dir, "StrategicData.csv")
        )
        self._normal_csv_path: str = os.path.abspath(
            os.path.join(files_dir, "NormalNumberData.csv")
        )
