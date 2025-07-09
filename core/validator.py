# core/validator.py
# # This module handles the validation of user configurations and API tokens.

# utils/u3_data_process.py [utilities / data process]

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Union

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Removed for production best practice
from config.settings import Settings  
from utils.logger import get_logger 
from utils.file_ops import DirManager 

logger = get_logger(__file__)


class DataValidator:
    def __init__(self) -> None:
        self.dir_manager: DirManager = DirManager()
        self.data_config: Settings = Settings()
        # Retrieve all important data forge file paths as attributes from DirManager
        paths = (
            self.dir_manager.get_data_forge_paths()
        )  # Get all relevant paths as a dictionary

        # Assign each path to an attribute for easy access throughout the class
        self.pink_data_dir: Path = paths["pink_data_dir"]  # Pink data directory
        self.normal_data_dir: Path = paths["normal_data_dir"]  # Normal data directory
        self.random_data_dir: Path = paths["random_data_dir"]  # Random data directory
        self.strategic_data_dir: Path = paths[
            "strategic_data_dir"
        ]  # Strategic data directory
        self.processed_data_dir: Path = paths[
            "processed_data_dir"
        ]  # Processed data directory
        self.all_number_file: Path = paths["all_number_base_data_file"]
        # All number base data file
        self.normal_file: Path = paths["normal_number_base_data_file"]
        # Normal number base data file
        self.pink_file: Path = paths["pink_number_base_data_file"]
        # Pink number base data file
        self.strategic_file: Path = paths["strategic_number_base_data_file"]
        # Strategic number base data file
        self.report_path: Path = paths["report_path"]  # Report file path
        self.processed_count: int = 0
        # Initialize column mappings
        self.column_mapping: Dict[str, str] = {
            "Not Pink Number": "PNum",
            "NNum": "PNum",
            "N_Num": "PNum",
            "NPNum": "PNum",
            "Pink Number": "PNum",
            "Server Time": "STime",
            "Local Time": "LTime",
            "Local Date": "LDate",
        }
        # Initialize column sets
        self.desired_columns: Set[str] = {
            "PNum",
            "STime",
            "LTime",
            "LDate",
            "TN",
            "TDiff",
            "RoundNo",
            "TimePeriod",
        }
        self.wanted_columns: List[str] = list(self.desired_columns)

    def _report_file_exists(self) -> bool:
        """
        Check if the report file exists.

        Returns:
            bool: True if the report file exists, False otherwise.
        """
        # Use self.report_path instead of self.data_config.report_path for clarity
        return self.report_path.exists()

    def _initialize_report_file(self) -> None:
        """
        Initialize the report file with a header.

        Raises:
            OSError: If the file cannot be created or written.
        """
        try:
            with open(self.report_path, "w") as f:
                # Write header with timestamp
                f.write(
                    f"DataForge Processing Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n")
            logger.info(f"Initialized report file at {self.report_path}")
        except OSError as e:
            logger.error(f"Failed to initialize report file: {e}")
            raise  # escalate, as report file is critical

    def _process_single_file(self, file: Path) -> bool:
        """
        Process a single file: load, validate, process, and save.

        Args:
            file (Path): The file to process.

        Returns:
            bool: True if processed and saved successfully, False otherwise.
        """
        try:
            logger.info(f"Processing file: {file}")

            # Load data from CSV file
            try:
                data = pd.read_csv(file)
            except pd.errors.EmptyDataError:
                logger.warning(f"File is empty or corrupt: {file}")
                return False
            except FileNotFoundError:
                logger.error(f"File not found: {file}")
                return False
            except pd.errors.ParserError as e:
                logger.error(f"Parsing error in file {file}: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error loading file {file}: {e}")
                return False

            if data.empty:
                logger.warning(f"File is empty: {file}")
                return False

            logger.info(f"Data loaded successfully: {file}")

            # Clean and process data
            try:
                processed_data = self._process_dataframe(data)
            except Exception as e:
                logger.error(f"Error during data processing for {file}: {e}")
                return False

            if processed_data is None:
                logger.error(f"Failed to process data: {file}")
                return False

            # Save processed data
            try:
                if self.clean_and_save_data(
                    processed_data, self.processed_data_dir, file
                ):
                    logger.debug(f"Successfully processed: {file}")
                    return True
                else:
                    logger.error(f"Failed to save processed data: {file}")
                    return False
            except OSError as e:
                logger.error(f"File system error while saving {file}: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error while saving {file}: {e}")
                return False

        except Exception as e:
            # Catch-all for any unexpected error in the file processing pipeline
            logger.error(f"Critical error processing file {file}: {e}")
            return False

    def check_pink_data_dir(self) -> List[Path]:
        """
        Check and validate the data directory for AllNumber*.csv files.

        This function ensures the processed data directory exists, checks for the presence
        of AllNumber*.csv files in the normal data directory, and logs the process.
        It is split into smaller helper functions for clarity and anti-error structure.

        Returns:
            List[Path]: List of AllNumber*.csv file paths found, or an empty list if none found.
        """

        def _ensure_processed_dir_exists(processed_dir: Path) -> None:
            """Ensure the processed data directory exists, create if not."""
            try:
                processed_dir.mkdir(
                    parents=True, exist_ok=True
                )  # create directory if not exists
                logger.info(f"Validated processed data directory: {processed_dir}")
            except PermissionError as e:
                logger.error(
                    f"Permission denied while creating processed data directory: {e}"
                )
                raise
            except FileNotFoundError as e:
                logger.error(
                    f"Parent directory does not exist for processed data directory: {e}"
                )
                raise
            except OSError as e:
                logger.error(f"OS error while creating processed data directory: {e}")
                raise

        def _get_allnumber_files(normal_data_dir: Path) -> List[Path]:
            """Get all AllNumber*.csv files from the normal data directory."""
            files: List[Path] = []
            if normal_data_dir.exists():
                try:
                    dir_files = list(
                        normal_data_dir.glob("AllNumber*.csv")
                    )  # search for AllNumber*.csv
                    if dir_files:
                        logger.info(
                            f"Found {len(dir_files)} AllNumber files in {normal_data_dir.name}"
                        )
                        files.extend(dir_files)
                except PermissionError as e:
                    logger.error(
                        f"Permission denied while accessing {normal_data_dir}: {e}"
                    )
                except OSError as e:
                    logger.error(f"OS error while accessing {normal_data_dir}: {e}")
            else:
                logger.warning(f"Data directory does not exist: {normal_data_dir}")
            return files

        # --- Main logic starts here ---
        try:
            # Step 1: Ensure processed data directory exists
            _ensure_processed_dir_exists(self.processed_data_dir)

            # Step 2: Get AllNumber*.csv files from normal data directory
            files = _get_allnumber_files(self.normal_data_dir)

            # Step 3: Handle case where no files are found
            if not files:
                logger.warning("No AllNumber files found. Please download them.")
                return []

            # Step 4: Log and return found files
            logger.info(f"Found {len(files)} AllNumber files to process")
            return files

        except (PermissionError, FileNotFoundError, OSError) as e:
            # Handle known filesystem-related errors
            logger.error(f"Filesystem error while checking data directories: {e}")
            return []
        # No general Exception catch here to avoid swallowing unexpected errors

    @staticmethod
    def check_column_errors(
        data: pd.DataFrame, column_name: str, display_name: str
    ) -> bool:
        """Check for null values in a specified column.

        Pros:
        - More detailed error reporting
        - Better input validation
        - Clearer return values

        Cons:
        - Additional validation overhead
        """
        try:
            # Validate input
            if not isinstance(data, pd.DataFrame):
                logger.error("Invalid input: data must be a pandas DataFrame")
                return False

            if not isinstance(column_name, str):
                logger.error("Invalid input: column_name must be a string")
                return False

            # Check column existence
            if column_name not in data.columns:
                logger.error(f"Column '{display_name}' not found in dataframe")
                return False

            # Check for null values
            null_count = data[column_name].isnull().sum()
            if null_count > 0:
                logger.warning(
                    f"Column '{display_name}' contains {null_count} null values"
                )
                return False

            return True

        except Exception as e:
            logger.debug(f"Error checking column errors: {e}")
            return False

    @staticmethod
    def date_parser(date_str: str) -> datetime.date:
        """Parse date string and return a date object.

        Pros:
        - More robust date parsing
        - Better error handling
        - Support for multiple formats
        - Clearer return types

        Cons:
        - Additional parsing overhead
        """
        try:
            # Validate input
            if not date_str or not isinstance(date_str, str):
                logger.debug("Invalid date string input")
                return datetime(1970, 1, 1).date()

            # Clean input
            date_str = date_str.strip()

            # Try different date formats
            formats = [
                "%Y-%m-%d",
                "%Y:%m:%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
                "%Y.%m.%d",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

            logger.debug(f"Unrecognized date format: {date_str}")
            return datetime(1970, 1, 1).date()

        except Exception as e:
            logger.debug(f"Error parsing date: {e}")
            return datetime(1970, 1, 1).date()

    @staticmethod
    def time_parser(time_str: str) -> Optional[datetime.time]:
        """Parse time string and return a time object.

        Pros:
        - Better error handling
        - More robust parsing
        - Clearer return types
        - Better validation

        Cons:
        - Additional parsing overhead
        """
        try:
            # Validate input
            if (
                pd.isna(time_str)
                or not isinstance(time_str, str)
                or not time_str.strip()
            ):
                return None

            # Clean input
            time_str = time_str.strip()

            # Try different time formats
            formats = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt).time()
                except ValueError:
                    continue

            logger.debug(f"Unrecognized time format: {time_str}")
            return None

        except Exception as e:
            logger.debug(f"Error parsing time: {e}")
            return None

    @staticmethod
    def get_weekday_or_invalid(date: pd.Series) -> Union[int, str]:
        """Get weekday index or 'Invalid Date' if invalid.

        Pros:
        - Better error handling
        - Clearer return types
        - Better validation

        Cons:
        - Additional validation overhead
        """
        try:
            if pd.notnull(date):
                return date.weekday()
            return "Invalid Date"
        except Exception as e:
            logger.debug(f"Error getting weekday: {e}")
            return "Invalid Date"

    @staticmethod
    def create_time_period(data: pd.DataFrame) -> pd.DataFrame:
        """Create a 'TimePeriod' column based on the 'STime' column.

        Pros:
        - Better error handling
        - More efficient processing
        - Better validation
        - Safer operations
        - Proper DataFrame copying

        Cons:
        - Additional processing overhead
        """
        try:
            # Create a copy of the DataFrame to avoid SettingWithCopyWarning
            data = data.copy()

            # Create hour column using .loc
            data.loc[:, "Hour"] = data["STime"].apply(
                lambda x: x.hour if pd.notna(x) else np.nan
            )

            # Create time period using .loc
            data.loc[:, "TimePeriod"] = data["Hour"].apply(
                lambda x: (
                    "Morning"
                    if 6 <= x < 12
                    else (
                        "Afternoon"
                        if 12 <= x < 18
                        else "Evening" if 18 <= x < 24 else "Night"
                    )
                )
            )

            # Clean up using .loc
            data = data.drop(columns=["Hour"])
            return data

        except Exception as e:
            logger.error(f"Error creating time period: {e}")
            return data

    def map_to_day_order(self, day_number: int) -> str:
        """Map a weekday number to a named day.

        Pros:
        - Better input validation
        - Clearer error handling
        - More maintainable code

        Cons:
        - Additional validation overhead
        """
        try:
            if not isinstance(day_number, int):
                logger.warning(f"Invalid day number type: {type(day_number)}")
                return "Invalid Date"

            if 0 <= day_number < len(self.data_config.day_order):
                return self.data_config.day_order[day_number]

            logger.warning(f"Day number out of range: {day_number}")
            return "Invalid Date"

        except Exception as e:
            logger.debug(f"Error mapping day number: {e}")
            return "Invalid Date"

    def calculate_time_diff(self, row: pd.Series) -> Optional[int]:
        """Calculate time difference in seconds between STime and LTime.

        Pros:
        - Better type hints
        - More robust error handling
        - Clearer return values
        - Better documentation
        - Handles negative time differences by taking absolute value

        Cons:
        - Slightly more complex logic
        """
        try:
            l_time, s_time = row.get("LTime"), row.get("STime")

            # Validate input values
            if pd.isna(l_time) or pd.isna(s_time):
                logger.debug("Missing time values in row")
                return None

            # Calculate time difference
            l_time_dt = datetime.combine(self.data_config.dummy_date, l_time)
            s_time_dt = datetime.combine(self.data_config.dummy_date, s_time)
            diff_seconds = int((l_time_dt - s_time_dt).total_seconds())

            # Take absolute value if negative
            if diff_seconds < 0:
                diff_seconds = abs(diff_seconds)

            return diff_seconds

        except Exception as e:
            logger.debug(f"Error calculating time difference: {e}")
            return None

    def _generate_file_report(self, data: pd.DataFrame, file_path: Path) -> None:
        """Generate a detailed report about the processed file and append it to the main report file.

        Pros:
        - Better visibility into data processing
        - Helps identify data quality issues
        - Provides useful statistics
        - Improves debugging capabilities
        - Maintains a single report file for all processing runs

        Cons:
        - Additional processing overhead
        - Additional disk I/O
        """
        try:
            report_lines = []

            # Add report header with separator
            report_lines.append("\n" + "=" * 80)
            report_lines.append("📊 File Processing Report")
            report_lines.append(f"📁 File: {file_path.name}")
            report_lines.append(
                f"📊 Shape: {data.shape[0]} rows x {data.shape[1]} columns"
            )
            report_lines.append(
                f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Column statistics
            report_lines.append("\n📈 Column Statistics:")
            for col in data.columns:
                null_count = data[col].isnull().sum()
                unique_count = data[col].nunique()
                dtype = data[col].dtype
                report_lines.append(f"  - {col}:")
                report_lines.append(f"    Type: {dtype}")
                report_lines.append(
                    f"    Null values: {null_count} ({null_count/data.shape[0]*100:.2f}%)"
                )
                report_lines.append(f"    Unique values: {unique_count}")

            # Time difference statistics
            if "TDiff" in data.columns:
                td_stats = data["TDiff"].describe()
                report_lines.append("\n⏱️ Time Difference Statistics:")
                report_lines.append(f"  - Min: {td_stats['min']:.2f} seconds")
                report_lines.append(f"  - Max: {td_stats['max']:.2f} seconds")
                report_lines.append(f"  - Mean: {td_stats['mean']:.2f} seconds")
                report_lines.append(f"  - Median: {td_stats['50%']:.2f} seconds")

            # Date range
            if "LDate" in data.columns:
                date_range = data["LDate"].agg(["min", "max"])
                report_lines.append("\n📅 Date Range:")
                report_lines.append(f"  - From: {date_range['min']}")
                report_lines.append(f"  - To: {date_range['max']}")

            # Time period distribution
            if "TimePeriod" in data.columns:
                period_counts = data["TimePeriod"].value_counts()
                report_lines.append("\n🕒 Time Period Distribution:")
                for period, count in period_counts.items():
                    report_lines.append(
                        f"  - {period}: {count} ({count/data.shape[0]*100:.2f}%)"
                    )

            # Ensure report directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)

            # Append report to the main report file
            with open(self.report_path, "a") as f:
                f.write("\n".join(report_lines) + "\n")

            # Also logger.info to console
            # logger.info('\n'.join(report_lines))
            logger.debug(f"Report appended to: {self.report_path}")

        except Exception as e:
            logger.debug(f"Error generating file report: {e}")

    def _process_dataframe(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Process a single dataframe with enhanced reporting and robust error handling.
        This function is split into smaller helper methods for clarity and maintainability.
        Each operation is wrapped with specific exception handling where possible.
        Returns:
            Optional[pd.DataFrame]: Processed DataFrame or None if errors occur.
        """

        # --- Helper Functions ---
        def _copy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
            # Create a copy to avoid SettingWithCopyWarning
            try:
                return df.copy()
            except AttributeError as e:
                logger.error(f"Failed to copy DataFrame: {e}")
                raise

        def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
            # Remove 'datetime' column if present and strip column names
            if "datetime" in df.columns:
                df = df.drop(columns=["datetime"])
            df.columns = df.columns.str.strip()
            return df

        def _drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
            # Drop duplicates based on 'RoundNo' and 'STime'
            try:
                original_rows = len(df)
                df = df.drop_duplicates(subset=["RoundNo"], keep="first")
                df = df.drop_duplicates(subset=["STime"], keep="first")
                dup_removed = original_rows - len(df)
                if dup_removed > 0:
                    logger.info(f"  - Removed {dup_removed} duplicate rows")
                return df
            except KeyError as e:
                logger.error(f"Missing column for duplicate removal: {e}")
                # Immediately stop processing if required column is missing
                return None

        def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
            # Rename columns using self.column_mapping, fallback to partial mapping on error
            try:
                return df.rename(columns=self.column_mapping)
            except (KeyError, TypeError) as e:
                logger.debug(f"Error renaming columns: {e}")
                return df.rename(
                    columns={
                        k: v for k, v in self.column_mapping.items() if k in df.columns
                    }
                )

        def _validate_required_columns(df: pd.DataFrame) -> bool:
            # Check for required columns and log errors
            for col, label in [
                ("LDate", "Local Date"),
                ("LTime", "Local Time"),
                ("STime", "Server Time"),
            ]:
                if not self.check_column_errors(df, col, label):
                    logger.error(f"Missing required column: {label} ({col})")
                    return False
            return True

        def _convert_columns(df: pd.DataFrame) -> pd.DataFrame:
            # Convert date and time columns using provided parsers
            try:
                df.loc[:, "LDate"] = df["LDate"].apply(self.date_parser)
                df.loc[:, "LTime"] = df["LTime"].apply(self.time_parser)
                df.loc[:, "STime"] = df["STime"].apply(self.time_parser)
            except KeyError as e:
                logger.error(f"Column missing during conversion: {e}")
                raise
            except ValueError as e:
                logger.error(f"Value error during date/time conversion: {e}")
                raise
            return df

        def _drop_unwanted_columns(df: pd.DataFrame) -> pd.DataFrame:
            # Drop 'DayName' and 'TimeDiff' columns if present
            for col in ["DayName", "TimeDiff"]:
                if col in df.columns:
                    df = df.drop(columns=[col])
            return df

        def _ensure_tn_column(df: pd.DataFrame) -> pd.DataFrame:
            # Ensure 'TN' column exists, create if missing
            if "TN" not in df.columns:
                try:
                    df.loc[:, "TN"] = (
                        df["LDate"]
                        .apply(self.get_weekday_or_invalid)
                        .apply(self.map_to_day_order)
                    )
                except KeyError as e:
                    logger.error(f"Cannot create 'TN' column, missing 'LDate': {e}")
                    raise
            return df

        def _calculate_time_diff(df: pd.DataFrame) -> pd.DataFrame:
            # Calculate time differences and handle negative values
            try:
                df.loc[:, "TDiff"] = df.apply(self.calculate_time_diff, axis=1)
                neg_time_rows = (df["TDiff"] < 0).sum()
                if neg_time_rows > 0:
                    df.loc[:, "TDiff"] = df["TDiff"].abs()
            except KeyError as e:
                logger.error(f"Error calculating time difference: {e}")
                raise
            return df

        def _ensure_roundno_column(df: pd.DataFrame) -> pd.DataFrame:
            # Ensure 'RoundNo' column exists, create if missing
            if "RoundNo" not in df.columns:
                current_id = 400000
                df.loc[:, "RoundNo"] = df.index + current_id
            return df

        def _create_time_period_safe(df: pd.DataFrame) -> pd.DataFrame:
            # Create time period column using self.create_time_period
            try:
                return self.create_time_period(df)
            except AttributeError as e:
                logger.error(f"create_time_period method not found: {e}")
                raise
            except Exception as e:
                logger.error(f"Error in create_time_period: {e}")
                raise

        def _generate_report_safe(df: pd.DataFrame) -> None:
            # Generate detailed report using self._generate_file_report
            try:
                self._generate_file_report(df, Path("processed_data"))
            except AttributeError as e:
                logger.error(f"_generate_file_report method not found: {e}")
            except Exception as e:
                logger.error(f"Error in _generate_file_report: {e}")

        # --- Main Processing Logic ---

        # Step 1: Copy DataFrame
        try:
            data = _copy_dataframe(data)
        except AttributeError:
            return None

        # Step 2: Clean columns (strip spaces from column names before any further processing)
        data = _clean_columns(data)
        logger.debug(
            f"[CLEANED COLUMNS] DataFrame columns after cleaning: {list(data.columns)}"
        )

        logger.info(f"\n🔄 Processing started with {len(data)} rows")

        # Step 3: Drop duplicates (stop immediately if error)
        data = _drop_duplicates(data)
        if data is None:
            # Error already logged, stop processing this file
            return None

        # Step 4: Rename columns
        data = _rename_columns(data)

        # Step 5: Validate required columns (stop immediately if error)
        if not _validate_required_columns(data):
            # Error already logged, stop processing this file
            return None

        # Step 6: Convert date/time columns
        try:
            data = _convert_columns(data)
        except (KeyError, ValueError):
            return None

        # Step 7: Drop unwanted columns
        data = _drop_unwanted_columns(data)

        # Step 8: Ensure TN column
        try:
            data = _ensure_tn_column(data)
        except KeyError:
            return None

        # Step 9: Calculate time differences
        try:
            data = _calculate_time_diff(data)
        except KeyError:
            return None

        # Step 10: Ensure RoundNo column
        data = _ensure_roundno_column(data)

        # Step 11: Create time period
        try:
            data = _create_time_period_safe(data)
        except (AttributeError, Exception):
            return None

        # Step 12: Generate detailed report
        _generate_report_safe(data)

        logger.info(f"\n✅ Processing complete. Final shape: {data.shape}")
        return data

    def clean_and_save_data(
        self, data: pd.DataFrame, output_dir: Path, file: Path
    ) -> bool:
        """
        Clean data and save it to the output directory with robust, anti-error structure.

        This function is split into smaller helpers for input validation, column checking,
        and file saving. Each step uses specific exception handling and logs errors for
        future maintenance and debugging.

        Returns:
            bool: True if data is successfully saved, False otherwise.
        """

        def _validate_inputs(data, output_dir, file) -> bool:
            # Validate that data is a DataFrame
            if not isinstance(data, pd.DataFrame):
                logger.error("Invalid input: data must be a pandas DataFrame")
                return False
            # Validate that output_dir is a Path object
            if not isinstance(output_dir, Path):
                logger.error("Invalid input: output_dir must be a Path object")
                return False
            # Validate that file is a Path object
            if not isinstance(file, Path):
                logger.error("Invalid input: file must be a Path object")
                return False
            return True

        def _check_required_columns(data) -> bool:
            # Check for missing required columns
            missing_columns = [
                col for col in self.wanted_columns if col not in data.columns
            ]
            if missing_columns:
                logger.error(f"Missing required columns: {', '.join(missing_columns)}")
                return False
            return True

        def _validate_data_not_empty(data, file) -> bool:
            # Ensure data is not empty before saving
            if data.empty:
                logger.error(f"No valid data to save for {file.name}")
                return False
            return True

        def _save_data_to_csv(data, output_dir, file) -> bool:
            # Save the DataFrame to CSV with error handling
            output_file_path = output_dir / f"Processed_{file.name}"
            try:
                data.to_csv(output_file_path, index=False)
                logger.debug(
                    f"Successfully saved processed data to: {output_file_path}"
                )
                return True
            except PermissionError as e:
                logger.error(
                    f"Permission denied when saving to {output_file_path}: {e}"
                )
                return False
            except FileNotFoundError as e:
                logger.error(f"Output directory not found for {output_file_path}: {e}")
                return False
            except OSError as e:
                logger.error(f"OS error while saving data to {output_file_path}: {e}")
                return False
            except pd.errors.EmptyDataError as e:
                logger.error(
                    f"Pandas empty data error while saving {output_file_path}: {e}"
                )
                return False
            except Exception as e:
                # Catch-all for any other unexpected error during save
                logger.error(
                    f"Unexpected error while saving data to {output_file_path}: {e}"
                )
                return False

        # --- Main logic starts here ---
        # Step 1: Validate all inputs
        if not _validate_inputs(data, output_dir, file):
            return False

        # Step 2: Check for required columns
        if not _check_required_columns(data):
            return False

        # Step 3: Validate data is not empty
        if not _validate_data_not_empty(data, file):
            return False

        # Step 4: Save data to CSV with robust error handling
        return _save_data_to_csv(data, output_dir, file)

    def process_data(self) -> bool:
        logger.info("Starting process_data pipeline.")
        if not self._report_file_exists():
            logger.debug("Report file does not exist. Initializing report file.")
            self._initialize_report_file()
        files = self.check_pink_data_dir()
        logger.debug(f"Files to process: {files}")
        if not files:
            logger.warning("No files to process")
            return False
        total_files = len(files)
        processed_count = 0
        for file in files:
            logger.info(f"Processing file: {file}")
            # Log file existence and size
            if not file.exists():
                logger.error(f"File does not exist: {file}")
                continue
            logger.debug(f"File size: {file.stat().st_size} bytes")
            # Try to load the data
            try:
                data = pd.read_csv(file)
                logger.debug(
                    f"Loaded DataFrame from {file}: shape={data.shape}, columns={list(data.columns)}"
                )
            except Exception as e:
                logger.error(f"Failed to load DataFrame from {file}: {e}")
                continue
            # Log before processing
            logger.debug(
                f"[DEEP TRACE] DataFrame before processing: shape={data.shape}, columns={list(data.columns)}"
            )
            if self._process_single_file(file):
                processed_count += 1
                logger.debug(f"[DEEP TRACE] Successfully processed file: {file}")
            else:
                logger.warning(f"Failed to process file: {file}")
        logger.info(
            f"Processing complete. {processed_count}/{total_files} files processed successfully"
        )
        return processed_count > 0


if __name__ == "__main__":
    try:
        dprocess = DataValidator()
        success = dprocess.process_data()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
