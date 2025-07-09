# utils/file_ops.py
# This module manages directories and files: creation, validation, and existence checks.
# It also provides utility functions to return directory and file locations for data storage.

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime
from utils import get_logger


# Singleton pattern for DirManager with type annotations for type safety and clarity
class DirManager:
    """
    Singleton class to manage all directories and files needed for the codebase.
    Handles creation, validation, and retrieval of paths for data and files.
    """

    _instance: Optional["DirManager"] = None  # type: ignore

    def __new__(cls: type, *args: Any, **kwargs: Any) -> "DirManager":
        # Ensure only one instance exists (singleton)
        if cls._instance is None:
            cls._instance = super(DirManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Initialize logger for this class
        self.logger = get_logger(__file__)
        # NOTE: DataForgeConfig is called without required arguments (see linter error)
        # This will cause a runtime error unless DataForgeConfig provides defaults for all arguments.
        self._setup_paths()

    def _setup_paths(self) -> None:
        """
        Set up all required paths and ensure base directories exist.
        """
        self.root: Path = self.get_project_root()  # Project root directory
        self.current_date: str = datetime.now().strftime(
            "%Y-%m-%d"
        )  # Current date string for report file naming

        # Data storage root
        self.data_source: Path = self.root / "DATA_STORAGE"
        self.data_forge_path: Path = self.data_source / "DATA_FORGE"
        self.scraper_data_path: Path = self.data_source / "SCRAPER_DATA"
        self.scraper_files_path: Path = self.scraper_data_path / "Files"
        self.scraper_infos_path: Path = self.scraper_data_path / "Infos"

        # Directory paths
        self.pink_data_dir: Path = self.data_forge_path / "PINK_DATA_DIR"
        self.normal_data_dir: Path = self.data_forge_path / "NORMAL_DATA_DIR"
        self.random_data_dir: Path = self.data_forge_path / "RANDOM_DATA_DIR"
        self.strategic_data_dir: Path = self.data_forge_path / "STRATEGIC_DATA_DIR"
        self.processed_data_dir: Path = self.data_forge_path / "PROCESSED_DATA_DIR"
        self.info_dir: Path = self.data_forge_path / "INFO"
        self.data_dir: Path = self.data_forge_path / "DATA"

        # File paths
        self.all_number_file: Path = self.normal_data_dir / "base_data_all_number.csv"
        self.normal_file: Path = self.normal_data_dir / "base_data_normal_number.csv"
        self.pink_file: Path = self.pink_data_dir / "base_data_pink_data.csv"
        self.strategic_file: Path = (
            self.strategic_data_dir / "base_data_strategic_data.csv"
        )

        # Special files
        self.data_combined_path: Path = self.processed_data_dir / "Data_Combined.csv"
        self.df_report_file: Path = self.info_dir / f"bt_report_{self.current_date}.txt"
        self.api_token_path: Path = self.data_dir / "api_token.json"
        self.base_file: Path = self.data_dir / "base_data.csv"
        self.csv_output_file: Path = self.data_dir / "output_prediction.csv"
        self.json_output_file: Path = self.data_dir / "output_prediction.json"

        # List of base directories to ensure exist
        self._base_dirs: List[Path] = [
            self.data_forge_path,
            self.pink_data_dir,
            self.normal_data_dir,
            self.random_data_dir,
            self.strategic_data_dir,
            self.processed_data_dir,
            self.data_dir,
            self.info_dir,
        ]
        self.create_dirs()

    def get_project_root(self) -> Path:
        """
        Get the absolute path to the project root directory.
        """
        return Path(__file__).parent.parent

    def ensure_path_exists(self, path: Path, is_file: bool = False) -> Path:
        """
        Ensure a directory or file's parent directory exists before accessing it.
        Args:
            path: Path to check/create
            is_file: Whether the path represents a file (True) or directory (False)
        Returns:
            The original path after ensuring its parent directory exists
        """
        try:
            if is_file:
                # For files, ensure parent directory exists
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # For directories, create if not exists
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created directory: {path}")
        except Exception as e:
            self.logger.error(f"Error ensuring path exists: {e}")
        return path

    def create_dirs(self) -> None:
        """
        Create all required base directories if they don't exist.
        """
        for dir_path in self._base_dirs:
            self.ensure_path_exists(dir_path)

    def get_data_forge_paths(self) -> Dict[str, Path]:
        """
        Get all important data forge file paths, ensuring their parent directories exist.
        Returns:
            dict: Mapping of file description to Path
        """
        paths: Dict[str, Path] = {
            "api_token": self.api_token_path,
            "data_forge_data_dir": self.data_forge_path,
            "pink_data_dir": self.pink_data_dir,
            "normal_data_dir": self.normal_data_dir,
            "random_data_dir": self.random_data_dir,
            "strategic_data_dir": self.strategic_data_dir,
            "processed_data_dir": self.processed_data_dir,
            # data file paths
            "all_number_base_data_file": self.all_number_file,
            "normal_number_base_data_file": self.normal_file,
            "pink_number_base_data_file": self.pink_file,
            "strategic_number_base_data_file": self.strategic_file,
            # special file paths
            "base_data_file": self.base_file,
            "report_path": self.df_report_file,
            "csv_output_file": self.csv_output_file,
            "json_output_file": self.json_output_file,
        }
        for name, path in paths.items():
            # Ensure parent directories for all files exist
            self.ensure_path_exists(path, is_file=True)
        return paths

    def check_data_forge_files_exist(self) -> str:
        """
        Check if data forge files and directories exist, log their status, and return status information.
        Returns:
            str: Status information about data forge files and directories.
        """
        paths: Dict[str, Path] = self.get_data_forge_paths()
        status_info: List[str] = []
        for name, path in paths.items():
            if not path.exists():
                msg: str = f"File or directory '{name}' DOES NOT EXIST at {path}"
                self.logger.critical(msg)  # Log missing file/dir info
                status_info.append(msg)
            else:
                msg: str = f"File or directory '{name}' EXISTS at {path}"
                self.logger.debug(msg)  # Log existence info
                status_info.append(msg)
        return "\n".join(status_info)

    def get_destination_dir(self, original_name: str) -> Path:
        """
        Given a file name, return the full file path if it matches a known file, otherwise return the default directory path.
        Args:
            original_name: The name of the file to categorize
        Returns:
            Path: The full file path (if known) or the directory where the file should be placed (if unknown)
        """
        try:
            # Check if the input is a string, else return the default directory
            if not isinstance(original_name, str):
                self.logger.error("Invalid file name type")
                return self.normal_data_dir
            # Normalize the file name for comparison
            original_name_lc: str = original_name.lower()
            self.logger.info(f"Categorizing file: {original_name_lc}")

            # Mapping of known file names to their full file paths
            known_files: Dict[str, Path] = {
                "allnumber.csv": self.all_number_file,  # base_data_all_number.csv
                "normalnumberdata.csv": self.normal_file,  # base_data_normal_number.csv
                "pinkdata.csv": self.pink_file,  # base_data_pink+data.csv
                "strategicdata.csv": self.strategic_file,  # base_data_strategic_data.csv
            }
            # If the file name is known, return its full file path
            if original_name_lc in known_files:
                self.logger.info(
                    f"Matched known file: {original_name_lc}, returning file path: {known_files[original_name_lc]}"
                )
                return known_files[original_name_lc]
            # If not known, return the default directory
            self.logger.info(
                "File name not recognized, returning default directory path (NORMAL_DATA_DIR)"
            )
            return self.normal_data_dir
        except Exception as e:
            self.logger.error(f"Error getting destination directory: {e}")
            return self.normal_data_dir

    def get_resource_path(self, relative_path: str) -> Path:
        """
        Get absolute path to resource, works for dev and for PyInstaller bundle.
        Args:
            relative_path: Relative path from project root
        Returns:
            Path: Absolute path
        """
        base_path: Path
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller support
            base_path = Path(sys._MEIPASS)  # type: ignore
        else:
            base_path = self.root
        return base_path / relative_path

    @property
    def data_source_path(self) -> Path:
        # Returns the path to the Data_Source directory
        return self.get_resource_path("Data_Source")

    @property
    def drivers_path(self) -> Path:
        # Returns the path to the Drivers directory
        return self.get_resource_path("Drivers")


# # Usage example (do not include in production):
# dir_manager = DirManager()
# # print(dir_manager.check_data_forge_files_exist())
# original_name = "strategicdata.csv"
# dest_dir: Path = dir_manager.get_destination_dir(original_name)
# print(dest_dir)
# print(dir_manager.get_data_forge_paths()["api_token"])
