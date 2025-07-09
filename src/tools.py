import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any  # import at the top if not already present


@dataclass
class ScraperConfig:
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
