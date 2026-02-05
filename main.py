# Auto_uploader/main.py
"""
Our entry point
Makee llc: Auto File committer and Git hub repo syncing system

"""

import sys
import time
from datetime import datetime

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.service import AutoCommitter


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
