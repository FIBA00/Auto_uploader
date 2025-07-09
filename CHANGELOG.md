# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

- /

## [1.0.0] - 2024-05-20

### Added

- Log file uploading to the GitHub repository for maintenance and model training
- Memory management for `last_saved_numbers` set with size limit (1000 entries)
- Comprehensive error handling and recovery mechanisms
- Data validation and integrity checks
- Backup mechanism for important data files
- Resource cleanup methods across all components
- Type annotations throughout the codebase
- Signal handlers for graceful shutdowns

### Changed

- Improved the GitSyncer service with better error handling
- Enhanced the restart system with timeout mechanism
- Optimized file path handling in AutoCommitter
- Restructured the main process loop for better reliability
- Improved overlay detection and handling
- Better organization of initialization steps with critical/non-critical designation

### Fixed

- Fixed memory leaks in data collection processes
- Corrected the restart verification method
- Improved handling of file descriptors during system restarts
- Fixed potential data loss during crashes

### Security

- Improved handling of credentials and sensitive information

## [0.0.1] - 2024-04-01

- Initial release of Raider V2 Data Scraping System

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/Fraol869/Raider_V2/compare/v1.0.0...HEAD
