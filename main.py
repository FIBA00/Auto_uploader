"""Makee llc: Auto File committer and Git syncing system"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from raider_tools import ScraperConfig #type: ignore


class AutoCommitter:
    """
        - AutoCommitter is a class that automates the process of committing files to a Git repository.
        It includes methods for fetching, pulling, adding, committing, pushing, and syncing changes.

    Attributes:
        repo_dir (str): The directory of the repository.
        commit_message (str): The commit message to use.
        branch_name (str): The branch name to use.
        files_to_commit (dict): A dictionary of files to commit with their paths.
    """

    def __init__(self):
        """
        Initialize AutoCommitter class with repository settings and file paths.
        """
        self.repo_dir = "."
        self.commit_message = "Makee llc data uploading to github system message."
        # Default branch name, will be updated during initialization
        self.branch_name = "main"
        # Use ScraperConfig for file paths
        self.sd = ScraperConfig()

        self.files_to_commit: Dict[str, str] = {
            "Pink Number Data": self.sd._pink_csv_path,
            "Normal Number data": self.sd._normal_csv_path,
            "All Number Data": self.sd._all_numbers_csv_path,
            "Strategic Number Data": self.sd._strategic_csv_path,
        }

        # Validate essential parameters
        if not os.path.isdir(self.repo_dir):
            raise ValueError(
                f"Repository directory '{self.repo_dir}' does not exist or is not a directory"
            )
        if not self.commit_message:
            raise ValueError("Commit message cannot be empty")
        if not self.branch_name:
            raise ValueError("Branch name cannot be empty")
        if not self.files_to_commit:
            raise ValueError("Files to commit cannot be empty")

        print(
            f"AutoCommitter initialized with {len(self.files_to_commit)} files to monitor"
        )
        print(f"Current Working dir: {os.getcwd()}")

        # Validate that we're in a git repository
        if not self.check_git_repository():
            raise ValueError(f"Directory '{self.repo_dir}' is not a git repository")

        # Determine the actual default branch name
        try:
            # First check if we have a "master" branch since it's commonly used
            all_branches = self.run_command("git branch -a")
            if "master" in all_branches:
                self.branch_name = "master"
                print(f"Found 'master' branch, using it as default")
            else:
                # Try to get the current branch name
                branch_output = self.run_command("git branch --show-current")
                if branch_output and "Error:" not in branch_output:
                    self.branch_name = branch_output.strip()
                    print(f"Using current branch: {self.branch_name}")
                else:
                    # If we can't get the current branch, try to get the default remote branch
                    remote_output = self.run_command("git remote show origin")
                    if "HEAD branch:" in remote_output:
                        for line in remote_output.split("\n"):
                            if "HEAD branch:" in line:
                                default_branch = line.split("HEAD branch:")[1].strip()
                                self.branch_name = default_branch
                                print(
                                    f"Using remote default branch: {self.branch_name}"
                                )
                                break

            print(f"Branch name set to: {self.branch_name}")
        except Exception as e:
            print(
                f"Could not determine branch name, using default '{self.branch_name}': {str(e)}"
            )

    def check_files(self) -> bool:
        """
        Checks if any of the files in the `files_to_commit` dictionary exist.

        Returns:
            bool: True if at least one file exists, False otherwise.
        """
        existing_files = []
        for name, path in self.files_to_commit.items():
            if not isinstance(path, str):
                raise TypeError(f"File path for '{name}' must be a string")
            if os.path.isfile(path):
                existing_files.append(name)

        if existing_files:
            print(
                f"Found {len(existing_files)} existing files to monitor: {', '.join(existing_files)}"
            )
            return True
        else:
            print("No files found to monitor")
            return False

    def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Executes a shell command in a subprocess and returns its output.

        Args:
            command (str): The command to execute.
            cwd (str, optional): The working directory to run the command in.

        Returns:
            str: The command output or error message.
        """
        if not command:
            raise ValueError("Command cannot be empty")

        print(f"Running: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.repo_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.stderr.strip()}"
            print(error_msg)
            return f"Error: {error_msg}"

    def git_fetch(self) -> bool:
        """
        Fetches updates from the remote repository.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            output = self.run_command("git fetch origin")
            print("Repository fetch completed")
            return "Error:" not in output
        except Exception as e:
            print(f"Failed to fetch from repository: {str(e)}")
            return False

    def git_pull(self) -> bool:
        """
        Pulls the latest changes from the remote repository for the specified branch.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            output = self.run_command(f"git pull origin {self.branch_name}")
            if "Error:" not in output:
                print("Repository pull completed")
                return True
            return False
        except Exception as e:
            print(f"Failed to pull from repository: {str(e)}")
            return False

    def git_status(self) -> Dict[str, list]:
        """
        Gets the status of the git repository.

        Returns:
            dict: A dictionary with 'staged', 'modified', and 'untracked' files.
        """
        status: Dict[str, list] = {"staged": [], "modified": [], "untracked": []}
        try:
            output = self.run_command("git status --porcelain")

            for line in output.splitlines():
                if not line.strip():
                    continue

                status_code = line[:2]
                file_path = line[3:].strip()

                if status_code.startswith("A") or status_code.startswith("M"):
                    status["staged"].append(file_path)
                elif status_code.startswith(" M"):
                    status["modified"].append(file_path)
                elif status_code.startswith("??"):
                    status["untracked"].append(file_path)

            return status
        except Exception as e:
            print(f"Failed to get repository status: {str(e)}")
            return status

    def git_add(self) -> bool:
        """
        Stages files for commit using Git.

        Returns:
            bool: True if at least one file was added, False otherwise.
        """
        any_added = False
        if not self.check_files():
            print("No files exist to add")
            return False

        for name, file_path in self.files_to_commit.items():
            if os.path.isfile(file_path):
                # Skip zero-length files
                if os.path.getsize(file_path) == 0:
                    print(f"Skipping empty file: {name}")
                    continue

                result = self.run_command(f"git add {file_path}")
                if "Error:" not in result:
                    print(f"Added {name} to staging")
                    any_added = True

        if any_added:
            print("Files staged successfully")
        else:
            print("No files were staged")

        return any_added

    def git_commit(self) -> bool:
        """
        Commits changes to the git repository if there are any staged changes.

        Returns:
            bool: True if a commit was made, False otherwise.
        """
        # Check for staged changes
        status = self.git_status()
        if not status["staged"]:
            print("No staged changes to commit")
            return False

        # Add timestamp to commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{self.commit_message} [{timestamp}]"

        # Use double quotes to handle single quotes in the message
        commit_command = f'git commit -m "{commit_message}"'
        result = self.run_command(commit_command)

        if "Error:" in result:
            print(f"Failed to commit: {result}")
            return False
        else:
            print("Changes committed successfully")
            return True

    def git_push(self) -> bool:
        """
        Pushes the current branch to the remote repository.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # First check if we're on the branch we want to push
            current_branch = self.run_command("git branch --show-current").strip()
            if current_branch != self.branch_name:
                print(
                    f"Currently on '{current_branch}', switching to '{self.branch_name}'"
                )

                # Check if the target branch exists locally
                local_branches = self.run_command("git branch")
                branch_exists_locally = (
                    f"* {self.branch_name}" in local_branches
                    or f"  {self.branch_name}" in local_branches
                )

                if branch_exists_locally:
                    # Branch exists, just switch to it
                    switch_result = self.run_command(f"git checkout {self.branch_name}")
                    if "Error:" in switch_result:
                        print(f"Failed to switch to existing branch: {switch_result}")
                        return False
                    print(f"Switched to existing branch '{self.branch_name}'")
                else:
                    # Check if branch exists on remote
                    remote_branches = self.run_command("git branch -r")
                    branch_exists_remotely = (
                        f"origin/{self.branch_name}" in remote_branches
                    )

                    if branch_exists_remotely:
                        # Branch exists remotely, track it
                        track_result = self.run_command(
                            f"git checkout -b {self.branch_name} --track origin/{self.branch_name}"
                        )
                        if "Error:" in track_result:
                            print(f"Failed to track remote branch: {track_result}")
                            return False
                        print(f"Tracking remote branch '{self.branch_name}'")
                    else:
                        # Create new branch
                        create_result = self.run_command(
                            f"git checkout -b {self.branch_name}"
                        )
                        if "Error:" in create_result:
                            print(f"Failed to create new branch: {create_result}")
                            return False
                        print(
                            f"Created and switched to new branch '{self.branch_name}'"
                        )

            # Check if we have commits
            has_commits = False
            try:
                commit_check = self.run_command("git rev-parse HEAD")
                has_commits = "Error:" not in commit_check
            except Exception:
                has_commits = False

            if not has_commits:
                print("No commits found. Creating initial commit.")
                # Create an empty commit if no commits exist
                empty_commit = self.run_command(
                    "git commit --allow-empty -m 'Initial commit'"
                )
                if "Error:" in empty_commit:
                    print(f"Failed to create initial commit: {empty_commit}")
                    return False

            # Try to push, handling the case where remote branch doesn't exist
            push_result = self.run_command(f"git push origin {self.branch_name}")

            # If push fails with "src refspec" error, try setting upstream
            if "src refspec" in push_result or "no upstream branch" in push_result:
                print(f"Remote branch not set up. Setting upstream branch.")
                upstream_result = self.run_command(
                    f"git push --set-upstream origin {self.branch_name}"
                )
                if "Error:" not in upstream_result:
                    print("Successfully set upstream and pushed changes")
                    return True
                else:
                    print(f"Failed to set upstream branch: {upstream_result}")
                    return False

            if "Error:" not in push_result:
                print("Changes pushed to remote repository")
                return True
            else:
                print(f"Failed to push: {push_result}")
                return False

        except Exception as e:
            print(f"Error pushing changes: {str(e)}")
            return False

    def git_sync(self) -> bool:
        """
        Synchronizes the local repository with the remote repository by pulling and pushing changes.

        Returns:
            bool: True if successful, False otherwise.
        """
        pull_success = self.git_pull()
        if not pull_success:
            print("Pull failed during sync, attempting push anyway")

        push_success = self.git_push()

        if pull_success and push_success:
            print("Repository sync completed successfully")
            return True
        else:
            print("Repository sync completed with warnings")
            return False

    def check_git_repository(self) -> bool:
        """
        Check if the current directory is a Git repository.

        Returns:
            bool: True if it's a git repository, False otherwise.
        """
        try:
            result = subprocess.run(
                "git rev-parse --is-inside-work-tree",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_dir,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error checking git repository: {str(e)}")
            return False

    def run(self) -> bool:
        """
        Executes the auto-commit process for the repository.

        Returns:
            bool: True if the process completed successfully, False otherwise.
        """
        print("Starting auto-commit process")

        # Save current directory
        original_dir = os.getcwd()

        try:
            # Change to repo directory
            os.chdir(self.repo_dir)

            # Sequence of operations with proper pauses between them
            operations = [
                ("Fetching", self.git_fetch, 1),
                ("Pulling", self.git_pull, 1),
                ("Adding", self.git_add, 1),
                ("Committing", self.git_commit, 1),
                ("Pushing", self.git_push, 1),
                ("Syncing", self.git_sync, 1),
            ]

            success = True
            for name, operation, delay in operations:
                print(f"Operation: {name}")
                try:
                    operation_success = operation()
                    if not operation_success and name in ["Adding", "Committing"]:
                        print(
                            f"Skipping remaining operations as {name.lower()} had no changes"
                        )
                        # No need to consider this a failure
                        break
                    success = success and operation_success
                    time.sleep(delay)
                except Exception as e:
                    print(f"Error during {name}: {str(e)}")
                    success = False

            if success:
                print("Auto-commit process completed successfully")
            else:
                print("Auto-commit process completed with warnings")

            return success

        except Exception as e:
            print(f"Error during auto-commit process: {str(e)}")
            return False
        finally:
            # Restore original directory
            os.chdir(original_dir)


if __name__ == "__main__":
    sync_interval = 120  # 2 minutes in seconds
    max_consecutive_errors = 3
    consecutive_errors = 0

    print("Starting GitSyncer service")

    try:
        while True:
            try:
                auto = AutoCommitter()
                success = auto.run()

                if success:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1

                if consecutive_errors >= max_consecutive_errors:
                    print(
                        f"Too many consecutive errors ({consecutive_errors}), will retry in {sync_interval * 2} seconds"
                    )
                    time.sleep(sync_interval * 2)  # Longer wait after errors
                    consecutive_errors = (
                        0  # Reset counter to avoid staying in error state
                    )
                else:
                    next_sync = datetime.now().timestamp() + sync_interval
                    next_sync_time = datetime.fromtimestamp(next_sync).strftime(
                        "%H:%M:%S"
                    )
                    print(f"Next sync at {next_sync_time}")
                    time.sleep(sync_interval)

            except Exception as e:
                print(f"Unexpected error in sync loop: {str(e)}")
                consecutive_errors += 1
                time.sleep(sync_interval)

    except KeyboardInterrupt:
        print("GitSyncer service stopped by user")
        sys.exit(0)
