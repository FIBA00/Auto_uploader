# core/uploader.py
# This module handles the uploading of files to GitHub repositories.

# utils/repo_handler.py

"""used to handle multiple repos and csv files to download them and show them to user,"""

import sys
import json
import time
import random
import string
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Removed for production best practice
from .t3_data_config import DataForgeConfig, UserConfig  # Use relative import for same-package utility
from ..utils.t1_log_manager import get_logger  # Use relative import for logger
from .t2_dir_manager import DirManager  # Use relative import for DirManager


logger = get_logger(__file__)


class RepoProcess:
    def __init__(self) -> None:
        self.user_configs: List[UserConfig] = []
        self.total_success: int = 0
        self.total_attempted: int = 0
        self.current_user: Optional[UserConfig] = None
        self.repo_url: Optional[str] = None
        self.headers: Optional[Dict[str, str]] = None
        self.dir_manager: DirManager = DirManager()
        self.config: DataForgeConfig = DataForgeConfig()
        self.user_config: UserConfig = UserConfig()

    # ------------------------------tools------------------------------------
    def setup_user_headers(self, user_config: UserConfig) -> bool:
        """
        Safely set up headers for a specific user.
        Handles all known exceptions explicitly and logs accordingly.

        Args:
            user_config (UserConfig): The user configuration object containing token and username.

        Returns:
            bool: True if headers were set up successfully, False otherwise.

        Maintenance Notes:
        - Handles AttributeError, TypeError, and KeyError separately for clarity.
        - Avoids catching general Exception to prevent masking unexpected bugs.
        - Logs all error cases for easier debugging and traceability.
        """
        try:
            # Ensure user_config has the required attributes
            if not hasattr(user_config, "token") or not hasattr(
                user_config, "username"
            ):
                logger.error("UserConfig missing 'token' or 'username' attribute")
                return False

            # Ensure token is a string and not empty
            if not isinstance(user_config.token, str) or not user_config.token.strip():
                logger.error(
                    f"Invalid or empty token for user: {getattr(user_config, 'username', 'unknown')}"
                )
                return False

            # Set up the headers for GitHub API requests
            self.headers = {
                "Authorization": f"token {user_config.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            # Set the current user for context in further operations
            self.current_user = user_config

            # Log successful header setup
            logger.info(f"Headers setup for user: {user_config.username}")
            return True

        except AttributeError as ae:
            # Handle missing attributes in user_config
            logger.error(
                f"AttributeError in setup_user_headers for user: {getattr(user_config, 'username', 'unknown')}: {ae}"
            )
            return False
        except TypeError as te:
            logger.error(
                f"TypeError in setup_user_headers for user: {getattr(user_config, 'username', 'unknown')}: {te}"
            )
            return False
        except KeyError as ke:
            # Handle missing keys if user_config is a dict-like object
            logger.error(
                f"KeyError in setup_user_headers for user: {getattr(user_config, 'username', 'unknown')}: {ke}"
            )
            return False
        # If you want to handle more specific exceptions, add them here with comments.
        # Do NOT catch general Exception here to avoid hiding programming errors.

    def check_rate_limit(self) -> Tuple[Optional[int], Optional[datetime]]:
        """Check GitHub API rate limit status.

        This function is structured to handle all known exceptions explicitly,
        providing robust error handling and clear logging for each failure mode.

        Pros:
        - Handles network, HTTP, JSON, and key errors separately
        - Logs specific error messages for each failure
        - Returns (None, None) on any failure for safe downstream handling

        Cons:
        - Slightly more verbose due to explicit exception handling
        """
        try:
            # Attempt to make the API request to check the rate limit
            # Add a timeout to prevent hanging forever; 15 seconds is a reasonable default for API calls
            response = requests.get(
                f"{self.config.git_api_url}/rate_limit",
                headers=self.headers,
                timeout=15,  # Timeout in seconds; adjust as needed for your environment
            )
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Connection error while checking rate limit: {ce}")
            return None, None
        except requests.exceptions.Timeout as te:
            logger.error(f"Timeout occurred while checking rate limit: {te}")
            return None, None
        except requests.exceptions.RequestException as re:
            logger.error(f"Request exception while checking rate limit: {re}")
            return None, None

        # Check for non-200 status code
        if response.status_code != 200:
            logger.error(
                f"Failed to check rate limit: {response.status_code} - {response.text}"
            )
            return None, None

        try:
            # Attempt to parse the JSON response
            limits = response.json()
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error while parsing rate limit response: {je}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error parsing rate limit JSON: {e}")
            return None, None

        try:
            core = limits["resources"]["core"]
            remaining = core["remaining"]
            reset_time = datetime.fromtimestamp(core["reset"])
        except KeyError as ke:
            logger.error(f"Missing expected key in rate limit response: {ke}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error extracting rate limit info: {e}")
            return None, None

        # Log the rate limit information for maintenance and monitoring
        logger.info(f"API calls remaining: {remaining}")
        logger.info(f"Rate limit resets at: {reset_time}")

        return remaining, reset_time

    def wait_for_rate_limit(self) -> bool:
        """Wait for rate limit reset if necessary.

        Pros:
        - Better rate limit handling
        - More efficient waiting
        - Clearer logging
        - Better error handling

        Cons:
        - Additional API call overhead

        This function is structured to handle all known exceptions explicitly for better error resistance and maintainability.
        """
        try:
            # Attempt to check the current rate limit status
            remaining, reset_time = self.check_rate_limit()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as net_exc:
            logger.error(f"Network error while checking rate limit: {net_exc}")
            return False
        except requests.exceptions.RequestException as req_exc:
            logger.error(f"Request exception while checking rate limit: {req_exc}")
            return False
        except json.JSONDecodeError as json_exc:
            logger.error(f"JSON decode error while checking rate limit: {json_exc}")
            return False
        except KeyError as key_exc:
            logger.error(f"Key error while checking rate limit: {key_exc}")
            return False
        except Exception as e:
            # Catch-all for any other unexpected exceptions
            logger.error(f"Unexpected error in wait_for_rate_limit: {e}")
            return False

        # Handle the case where rate limit status could not be determined
        if remaining is None or reset_time is None:
            logger.warning("Could not determine rate limit status")
            return False

        # If no remaining API calls, wait until reset
        if remaining == 0:
            try:
                now = datetime.now()
                wait_time = (reset_time - now).total_seconds()
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit exceeded. Waiting {wait_time:.0f} seconds..."
                    )
                    time.sleep(wait_time + 1)  # Add 1 second buffer
                    return True
            except OverflowError as oe:
                logger.error(f"Overflow error during wait: {oe}")
                return False
            except ValueError as ve:
                logger.error(f"Value error during wait: {ve}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during wait: {e}")
                return False

        # If we did not need to wait, return False
        return False

    def find_csv_files(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find specific CSV files in repository contents, including subdirectories.

        This function is structured for robust error handling and maintainability.
        It breaks down the logic into smaller helper methods for clarity and easier testing.

        Returns:
            List[Dict[str, Any]]: List of found CSV file metadata dictionaries.
        """
        # List to collect found CSV files
        csv_files: List[Dict[str, Any]] = []

        # Log the number of items to be searched
        logger.info(f"Searching through {len(contents)} items")

        # Separate files and directories for processing
        try:
            files, directories = self._separate_files_and_dirs(contents)
        except KeyError as ke:
            logger.error(f"Malformed content item missing expected key: {ke}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during file/dir separation: {e}")
            return []

        # Process files: filter and collect target CSVs
        try:
            csv_files.extend(self._filter_target_csv_files(files))
        except Exception as e:
            logger.error(f"Error filtering target CSV files: {e}")

        # Process directories recursively
        for dir_item in directories:
            # Check rate limit before each directory traversal
            try:
                remaining, reset_time = self.check_rate_limit()
            except Exception as e:
                logger.error(f"Error checking rate limit: {e}")
                continue

            if remaining is None or remaining < 5:  # Keep a buffer of 5 calls
                logger.warning("Rate limit is low, waiting for reset...")
                try:
                    if not self.wait_for_rate_limit():
                        logger.error("Failed to wait for rate limit reset")
                        continue
                except Exception as e:
                    logger.error(f"Error during rate limit wait: {e}")
                    continue

            logger.info(f"Exploring directory: {dir_item.get('name', '[unknown]')}")
            try:
                dir_contents = self._get_directory_contents(dir_item)
                if dir_contents is not None:
                    # Recursively search the directory for CSV files
                    sub_csv_files = self.find_csv_files(dir_contents)
                    if sub_csv_files:
                        logger.info(
                            f"Found {len(sub_csv_files)} target files in {dir_item.get('name', '[unknown]')}"
                        )
                        csv_files.extend(sub_csv_files)
            except requests.exceptions.HTTPError as http_err:
                status_code = getattr(http_err.response, "status_code", None)
                if status_code == 403:
                    logger.warning(
                        f"Access forbidden for directory {dir_item.get('name', '[unknown]')}, skipping..."
                    )
                    continue
                logger.error(
                    f"HTTP error accessing directory {dir_item.get('name', '[unknown]')}: {http_err}"
                )
                continue
            except requests.exceptions.ConnectionError as ce:
                logger.error(
                    f"Connection error accessing directory {dir_item.get('name', '[unknown]')}: {ce}"
                )
                continue
            except requests.exceptions.Timeout as te:
                logger.error(
                    f"Timeout accessing directory {dir_item.get('name', '[unknown]')}: {te}"
                )
                continue
            except requests.exceptions.RequestException as re:
                logger.error(
                    f"Request exception accessing directory {dir_item.get('name', '[unknown]')}: {re}"
                )
                continue
            except json.JSONDecodeError as je:
                logger.error(
                    f"JSON decode error for directory {dir_item.get('name', '[unknown]')}: {je}"
                )
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error accessing directory {dir_item.get('name', '[unknown]')}: {e}"
                )
                continue

        # Sort files by name for consistency
        csv_files.sort(key=lambda x: x.get("name", ""))
        logger.info(f"Found {len(csv_files)} target files in total")
        return csv_files

    def _separate_files_and_dirs(
        self, contents: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Helper to separate files and directories, skipping ignored directories.

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (files, directories)
        """
        files = []
        directories = []
        for item in contents:
            item_type = item.get("type")
            item_name = item.get("name", "")
            if item_type == "file":
                files.append(item)
            elif item_type == "dir":
                # Skip ignored or hidden directories
                if item_name in self.config.ignore_dirs or item_name.startswith("."):
                    logger.info(f"Skipping ignored directory: {item_name}")
                    continue
                directories.append(item)
        return files, directories

    def _filter_target_csv_files(
        self, files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Helper to filter files for target CSVs based on config flags.

        Returns:
            List[Dict[str, Any]]: List of matching CSV file dicts.
        """
        target_files = []
        for item in files:
            file_name = item.get("name", "").lower()
            # Check if file matches any enabled processing flags
            if (
                (file_name == "allnumber.csv" and self.config.process_all_number)
                or (
                    file_name == "normalnumberdata.csv"
                    and self.config.process_normal_number
                )
                or (file_name == "pinkdata.csv" and self.config.process_pink_data)
                or (
                    file_name == "strategicdata.csv"
                    and self.config.process_strategic_data
                )
            ):
                logger.info(f"Found target file: {item.get('name', '[unknown]')}")
                target_files.append(item)
        return target_files

    def _get_directory_contents(
        self, dir_item: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Helper to fetch and decode the contents of a directory from the API.

        Returns:
            Optional[List[Dict[str, Any]]]: List of directory contents, or None on error.
        """
        dir_url = dir_item.get("url")
        if not dir_url:
            logger.error(f"Directory item missing 'url': {dir_item}")
            return None
        try:
            # Add a timeout to prevent indefinite hanging (default: 15 seconds)
            # This ensures the request will fail gracefully if the server is unresponsive.
            dir_response = requests.get(dir_url, headers=self.headers, timeout=15)
            dir_response.raise_for_status()  # Raises HTTPError for bad responses
            dir_contents = dir_response.json()
            if not isinstance(dir_contents, list):
                logger.error(
                    f"Directory contents not a list for {dir_item.get('name', '[unknown]')}"
                )
                return None
            return dir_contents
        except requests.exceptions.RequestException as re:
            logger.error(f"Request exception fetching directory contents: {re}")
            raise
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error fetching directory contents: {je}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching directory contents: {e}")
            raise

    def download_csv_files(self) -> bool:
        logger.info("Starting download_csv_files process.")
        all_success: bool = True  # Track if all downloads succeed
        for csv_file in getattr(self, "csv_files", []):
            try:
                logger.info(f"Processing file: {csv_file['name']}")
                file_url: str = csv_file["download_url"]
                original_name: str = csv_file["name"]
                dest_path: Path = self.dir_manager.get_destination_dir(original_name)
                logger.debug(f"Destination path resolved: {dest_path}")
                if dest_path.exists() and dest_path.is_file():
                    logger.warning(
                        f"Destination path {dest_path} is a file. Using its parent directory for saving downloaded file."
                    )
                    dest_dir = dest_path.parent
                elif dest_path.suffix == ".csv":
                    logger.warning(
                        f"Destination path {dest_path} looks like a file. Using its parent directory for saving downloaded file."
                    )
                    dest_dir = dest_path.parent
                else:
                    dest_dir = dest_path
                logger.debug(f"Final destination directory: {dest_dir}")
                dest_dir.mkdir(parents=True, exist_ok=True)
                random_suffix: str = self.generate_random_string()
                file_name: str = f"{original_name.split('.')[0]}_{random_suffix}.csv"
                file_path: Path = dest_dir / file_name
                logger.info(f"Downloading from {file_url} to {file_path}")
                with open(file_path, "wb") as f:
                    for chunk in requests.get(
                        file_url, stream=True, timeout=30
                    ).iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Successfully saved file to: {file_path}")
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Network error when downloading {csv_file.get('name', 'unknown')}: {e}"
                )
                all_success = False
                continue
            except IOError as e:
                logger.error(
                    f"File system error when saving {csv_file.get('name', 'unknown')}: {e}"
                )
                all_success = False
                continue
            except KeyError as e:
                logger.error(f"Missing expected key in csv_file dict: {e}")
                all_success = False
                continue
        logger.info(f"All downloads completed. Success: {all_success}")
        return all_success

    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """Generate a random string of specified length.

        Pros:
        - Better error handling
        - More secure random generation
        - Clearer return types

        Cons:
        - Additional generation overhead
        """
        try:
            if not isinstance(length, int) or length < 1:
                length = 8

            chars = string.ascii_letters + string.digits
            return "".join(random.choices(chars, k=length))

        except Exception as e:
            logger.debug(f"Error generating random string: {e}")
            return "default"

    # --------------------------------main process-----------------------------
    def _safe_setup_user_headers(self, user_config) -> bool:
        """
        Safely set up headers for a user, handling known exceptions.
        Returns True if successful, False otherwise.
        """
        try:
            if not self.setup_user_headers(user_config):
                logger.error(
                    f"Failed to setup headers for user: {user_config.username}"
                )
                return False
            return True
        except AttributeError as e:
            logger.error(
                f"Attribute error during header setup for {user_config.username}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error during header setup for {user_config.username}: {e}"
            )
            return False

    def _safe_check_and_wait_rate_limit(self) -> bool:
        """
        Safely check the rate limit and wait if necessary.
        Returns True if it's safe to proceed, False otherwise.
        """
        try:
            remaining, reset_time = self.check_rate_limit()
            if remaining is None or remaining < 10:  # Keep a buffer of 10 calls
                logger.warning("Rate limit is low, waiting for reset...")
                if not self.wait_for_rate_limit():
                    logger.error("Failed to wait for rate limit reset")
                    return False
            return True
        except AttributeError as e:
            logger.error(f"Attribute error during rate limit check: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during rate limit check: {e}")
            return False

    def _process_single_repository(self, repo_name: str) -> bool:
        """
        Process a single repository: fetch contents, find CSVs, and download them.
        Handles all known exceptions and logs accordingly.

        Returns:
            bool: True if repository processed successfully, False otherwise.
        """
        try:
            # Fetch contents of repository with a timeout to avoid hanging forever
            response = requests.get(
                self.repo_url, headers=self.headers, timeout=30
            )  # 30 seconds timeout prevents indefinite hanging
            response.raise_for_status()
            try:
                contents = response.json()
            except ValueError as e:
                logger.error(f"Failed to decode JSON for {repo_name}: {e}")
                return False

            if not contents:
                logger.info(f"Contents are empty for repository: {repo_name}")
                return False

            # Find and download CSV files
            self.csv_files = self.find_csv_files(contents)
            if self.csv_files:
                logger.info(f"Found {len(self.csv_files)} CSV files in {repo_name}")

                # Download files with retry logic
                success = self._download_csv_files_with_retries(repo_name)
                if success:
                    # NOTE: clog.FSuccess is undefined in the context, so using logger.info instead
                    logger.info(f"✅ Successfully processed repository: {repo_name}")
                    return True
                else:
                    logger.error(f"❌ Failed to process repository: {repo_name}")
                    return False
            else:
                logger.info(f"No CSV files found in {repo_name}")
                return False

        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, "status_code", None)
            if status_code == 404:
                logger.error(f"Repository {repo_name} not found (404)")
            elif status_code == 403:
                logger.warning(f"Access forbidden for {repo_name}, skipping... (403)")
            else:
                logger.error(f"HTTP error for {repo_name}: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {repo_name}: {e}")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {repo_name}: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {repo_name}: {e}")
            return False
        except KeyError as e:
            logger.error(f"Key error while processing {repo_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing {repo_name}: {e}")
            return False

    def _download_csv_files_with_retries(self, repo_name: str) -> bool:
        """
        Attempt to download CSV files with retry logic and exponential backoff.
        Returns True if download succeeds, False otherwise.
        """
        for attempt in range(self.config.max_repo_retries):
            try:
                if self.download_csv_files():
                    return True
                elif attempt < self.config.max_repo_retries - 1:
                    logger.warning(
                        f"Download failed, retrying... (Attempt {attempt + 2}/{self.config.max_repo_retries})"
                    )
                    time.sleep(2**attempt)  # Exponential backoff

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error during CSV download for {repo_name}: {e}")
            except IOError as e:
                logger.error(f"IO error during CSV download for {repo_name}: {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error during CSV download for {repo_name}: {e}"
                )
        return False

    def _repo_processing(self) -> bool:
        """
        Start the repository process to fetch and download CSV files from multiple repositories.
        This function is structured for robust error handling and maintainability.
        It delegates subtasks to helper methods for clarity and easier testing.

        Returns:
            bool: True if at least one repository was processed successfully, False otherwise.
        """
        # Check if user configurations are available
        if not self.user_configs:
            logger.error("No user configurations available")
            return False

        total_success = 0  # Track number of successful repository processes
        total_attempted = 0  # Track total repositories attempted

        # Process each user configuration
        for user_config in self.user_configs:
            logger.info(f"\n🔄 Processing user: {user_config.username}")

            # Setup headers for this user, skip if setup fails
            if not self._safe_setup_user_headers(user_config):
                continue

            # Process each repository for the user
            for repo_name in user_config.repos:
                total_attempted += 1
                logger.info(f"\n📁 Processing repository: {repo_name}")

                # Check and handle rate limit before proceeding
                if not self._safe_check_and_wait_rate_limit():
                    continue

                # Set up the repository URL for API requests
                self.repo_url = f"{self.config.git_api_url}/repos/{user_config.username}/{repo_name}/contents"
                logger.info(f"Repository URL set to: {self.repo_url}")

                # Process the repository and handle all known exceptions
                repo_success = self._process_single_repository(repo_name)
                if repo_success:
                    total_success += 1

        # Log summary of processing
        logger.info("\n📊 Repository Processing Summary:")
        logger.info(f"  - Total attempted: {total_attempted}")
        logger.info(f"  - Successfully processed: {total_success}")

        return total_success > 0


if __name__ == "__main__":
    try:
        repo_process: RepoProcess = RepoProcess()
        repo_process._repo_processing()
    except KeyboardInterrupt:
        logger.debug("User exited ")
        sys.exit(1)
