#utils/github_api.py
# utils/api_handler.py

"""This tool is used for handling api and config"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Removed for production best practice
from .t3_data_config import UserConfig  # Use relative import for same-package utility
from ..utils.t1_log_manager import get_logger  # Use relative import for logger
from .t2_dir_manager import DirManager  # Use relative import for DirManager

logger = get_logger(__file__)


class ApiProcess:
    def __init__(self) -> None:
        # Initialize directory manager for handling paths
        self.dir_manager: DirManager = DirManager()
        # Get the path to the API token/config file
        self.api_token_path = self.dir_manager.get_data_forge_paths()["api_token"]
        # Store validated user configurations
        self.user_configs: List[UserConfig] = []
        # Required fields for each user in the config
        self.required_user_fields: List[str] = ["username", "token", "repos"]
        logger.debug("ApiProcess initialized.")

    def _file_exists(self, path: Path) -> bool:
        logger.debug(f"Checking if file exists: {path}")
        exists = path.exists()
        if not exists:
            logger.error("API configuration file does not exist")
        else:
            logger.info(f"API configuration file exists: {path}")
        return exists

    def _read_json_file(self, path: Path) -> Optional[Dict[str, Any]]:
        logger.debug(f"Reading JSON config file: {path}")
        try:
            with open(path, "r", encoding="utf-8") as config_file:
                data = json.load(config_file)
                logger.info(f"Successfully loaded JSON config file: {path}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return None
        except FileNotFoundError:
            logger.error("API configuration file not found when attempting to open")
            return None
        except PermissionError:
            logger.error("Permission denied when reading API configuration file")
            return None
        except OSError as e:
            logger.error(f"OS error when reading API configuration file: {e}")
            return None

    def _validate_repositories_field(self, config_data: Dict[str, Any]) -> bool:
        logger.debug("Validating 'repositories' field in config data.")
        if "repositories" not in config_data:
            logger.error("Missing 'repositories' field in config")
            return False
        if not isinstance(config_data["repositories"], list):
            logger.error("'repositories' must be a list")
            return False
        if not config_data["repositories"]:
            logger.error("No repositories configured")
            return False
        logger.info("'repositories' field validated successfully.")
        return True

    def _validate_and_parse_user_configs(
        self, repositories: List[Dict[str, Any]]
    ) -> bool:
        logger.debug("Validating and parsing user configs.")
        self.user_configs.clear()
        for user_data in repositories:
            logger.debug(f"Parsing user config: {user_data}")
            if not isinstance(user_data, dict):
                logger.error("User configuration must be a dictionary")
                return False
            for field in self.required_user_fields:
                if field not in user_data:
                    logger.error(
                        f"Missing required field '{field}' in user configuration"
                    )
                    return False
            if not isinstance(user_data["repos"], list):
                logger.error("'repos' must be a list")
                return False
            try:
                user_config = UserConfig(
                    username=user_data["username"],
                    token=user_data["token"],
                    repos=user_data["repos"],
                )
                logger.info(f"Parsed UserConfig: {user_config}")
                self.user_configs.append(user_config)
            except Exception as e:
                logger.error(f"Failed to create UserConfig: {e}")
                return False
        logger.info(f"Total user configs parsed: {len(self.user_configs)}")
        return True

    def _log_success(self):
        # Log the successful loading of the API config
        total_repos = sum(len(u.repos) for u in self.user_configs)
        logger.info(
            f"API configuration loaded successfully: {len(self.user_configs)} users, {total_repos} repositories"
        )

    def load_api_config_file(self) -> Optional[Dict[str, Any]]:
        logger.info("Loading API configuration file...")
        # Step 1: Check if the config file exists
        if not self._file_exists(self.api_token_path):
            return None

        # Step 2: Read and parse the JSON config file
        config_data = self._read_json_file(self.api_token_path)
        if config_data is None:
            return None

        # Step 3: Validate the 'repositories' field
        if not self._validate_repositories_field(config_data):
            return None

        # Step 4: Validate and parse user configurations
        if not self._validate_and_parse_user_configs(config_data["repositories"]):
            return None

        # Step 5: Log success and return the config data
        self._log_success()
        logger.info("API configuration file loaded and validated.")
        return config_data


# ---------------- MAIN ENTRY FOR TESTING ----------------
def api_handler():
    """
    Standalone api_handler entry to test all ApiProcess functions.
    This will:
    - Instantiate ApiProcess
    - Test loading the API config file
    - logger.info results and log outputs
    """
    logger.info("=== Starting ApiProcess api_handler test entry ===")
    api_proc = ApiProcess()

    # Test: Check if config file exists
    logger.info(f"Testing _file_exists: {api_proc.api_token_path}")
    exists = api_proc._file_exists(api_proc.api_token_path)
    logger.info(f"Config file exists: {exists}")

    # Test: Read JSON file
    logger.info("Testing _read_json_file")
    config_data = api_proc._read_json_file(api_proc.api_token_path)
    logger.info(f"Config data loaded: {config_data is not None}")

    # Test: Validate repositories field
    if config_data:
        logger.info("Testing _validate_repositories_field")
        valid_repos = api_proc._validate_repositories_field(config_data)
        logger.info(f"Repositories field valid: {valid_repos}")

        # Test: Validate and parse user configs
        if valid_repos:
            logger.info("Testing _validate_and_parse_user_configs")
            valid_users = api_proc._validate_and_parse_user_configs(
                config_data["repositories"]
            )
            logger.info(f"User configs valid: {valid_users}")

    # Test: Full load_api_config_file
    logger.info("Testing load_api_config_file")
    loaded_config = api_proc.load_api_config_file()
    logger.info(f"Full config loaded: {loaded_config is not None}")

    # logger.info user configs if loaded
    if api_proc.user_configs:
        logger.info("User configs parsed:")
        for user in api_proc.user_configs:
            logger.info(f"  - Username: {user.username}, Repos: {user.repos}")

        # Additional check: log the total number of users and repos for clarity
        total_users = len(api_proc.user_configs)
        total_repos = sum(len(u.repos) for u in api_proc.user_configs)
        logger.info(
            f"Summary: {total_users} users, {total_repos} repositories (should match config file)"
        )

        # Assert for test: ensure the number of repos matches the config file for correctness
        # This is a test assertion, not for production
        expected_users = (
            len(config_data["repositories"])
            if config_data and "repositories" in config_data
            else 0
        )
        expected_repos = (
            sum(len(u["repos"]) for u in config_data["repositories"])
            if config_data and "repositories" in config_data
            else 0
        )
        if total_users != expected_users or total_repos != expected_repos:
            logger.error(
                f"Mismatch: Found {total_users} users and {total_repos} repos, but expected {expected_users} users and {expected_repos} repos from config!"
            )
        else:
            logger.info("User and repo counts match the config file.")

    logger.info("=== ApiProcess api_handler test entry complete ===")


# Only run api_handler if this file is executed directly (not imported)
if __name__ == "__main__":
    api_handler()
