# utils/t3_data_config.py [utilities tool / tool 3 data configuration ]
# DataForgeConfig is the central configuration dataclass for all tools.
# All directory/file paths are initialized using DirManager at startup.
# All tools should receive a reference to this config and use only the parts they need.

import os
import sys
import json
import time
import shutil
import random
import string
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set, Union


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
class DataForgeConfig:
    """
    Central configuration class for all tools in the system.
    All directory/file paths should be set at startup using DirManager.
    All other config fields (flags, tokens, etc.) are included here as well.
    Tools should only use this config, not DirManager directly.
    """

    # Processing flags for each file type
    process_all_number: bool = True
    process_normal_number: bool = False
    process_pink_data: bool = False
    process_strategic_data: bool = False
    # Repository processing configuration
    max_repo_retries: int = 2
    max_retries: int = 3
    git_api_url: str = "https://api.github.com"
    dummy_date: datetime = field(default_factory=lambda: datetime(2025, 1, 2).date())
    day_order: List[str] = field(
        default_factory=lambda: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    )
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
    # --- Prediction System Parameters ---
    required_columns: List[str] = field(
        default_factory=lambda: ["PNum", "STime", "LDate", "TN"]
    )
    timezone: str = "Africa/Addis_Ababa"
    tolerance_minutes: int = 2
    recency_weight: float = 0.7
    tolerance_seconds: int = tolerance_minutes * 60

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any  # import at the top if not already present


@dataclass
class Configs:
    _username: str = "0965475618"
    _password: str = "Sena##545063"
    _working_url: str = "https://www.betika.com/et/aviator"
    _test_url: str = "https://www.betika.com/et"
    _test_headless: bool = True
    _working_headless: bool = True
    _should_terminate: bool = False
    # ints for control
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 2
    wait_time: int = 20
    sys_count: int = 0
    max_sys_count: int = 30
    page_load_timeout: int = 240
    total_numbers_found: int = 0

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


def get_project_root():
    """Return the project root directory, compatible with PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
