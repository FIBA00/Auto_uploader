# utils/t1_log_manager.py [utilities tool / tool 1 logger manager]
# here we manage our logging system, with a single instance of the logger and a single instance of the handler
# also log files are managed[create, check, delete, etc]

from logging import (
    getLogger,
    StreamHandler,
    FileHandler,
    Formatter,
    INFO,
    DEBUG,
    WARNING,
    ERROR,
    CRITICAL,
)
import os
import time
from threading import Lock
from typing import Dict

# Global lock for thread safety in logger creation
_logger_lock = Lock()
# Dictionary to hold logger instances per script
_logger_instances: Dict[str, "LogManager"] = {}
# Default log directory
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)


class LogManager:
    """
    LogManager manages a single logger instance per script, with both console and file handlers.
    It also manages log file creation, cleanup, and formatting.
    """

    def __init__(self, script_path: str) -> None:
        # Extract script name for log file naming
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        # Ensure log directory exists
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        # Log file path
        self.log_file = os.path.join(LOG_DIR, f"{script_name}.log")
        # Create logger with script name
        self.logger = getLogger(script_name)
        self.logger.setLevel(DEBUG)  # Set default log level to DEBUG
        # Prevent duplicate handlers if logger already exists
        if not self.logger.handlers:
            # Console handler
            stream_handler = StreamHandler()
            stream_handler.setLevel(DEBUG)
            # File handler
            file_handler = FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(DEBUG)
            # Formatter for both handlers
            formatter = Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            stream_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            # Add handlers to logger
            self.logger.addHandler(stream_handler)
            self.logger.addHandler(file_handler)
        # Clean up old log files
        self.check_old_logs(LOG_DIR)

    def check_old_logs(self, log_file_path: str) -> None:
        """
        Check if there are any old logs and delete them.
        If older than 10 days, delete them.
        """
        for file in os.listdir(log_file_path):
            if file.endswith(".log"):
                file_path = os.path.join(log_file_path, file)
                if os.path.getmtime(file_path) < time.time() - 10 * 24 * 60 * 60:
                    self.delete_log_file(file_path)

    def delete_log_file(self, file_path: str) -> None:
        """
        Delete the specified log file if it exists.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Log the deletion for audit purposes
                self.logger.info(f"Deleted old log file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to delete log file {file_path}: {e}")

    def get_logger(self):
        """
        Return the logger instance managed by this LogManager.
        """
        return self.logger


# Module-level function for easy logger retrieval
# Usage: from utils.log_manager import get_logger; logger = get_logger(__file__)
def get_logger(script_path: str):
    """
    Retrieve a singleton logger for the given script path.
    Ensures only one logger per script, with file and console handlers.
    """
    with _logger_lock:
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        if script_name not in _logger_instances:
            _logger_instances[script_name] = LogManager(script_path)
        return _logger_instances[script_name].get_logger()


# logger = get_logger(__file__)
# logger.info("this is test message")
# logger.debug("this is test message")
# logger.error("this is test message")
# logger.warning("this is test message")
# logger.critical("this is test message")
