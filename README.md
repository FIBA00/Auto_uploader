# Raider V2 Data Scraping System

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

## 📝 Overview

Raider V2 is an advanced web scraping system designed to reliably extract, process, and store data from online gaming platforms with high efficiency and error tolerance. The system features robust error handling, automatic recovery mechanisms, and efficient data management to operate continuously even when facing connection issues, website changes, and other disruptions.

## 🧐 Key Features

- Real-time data extraction with categorization (Pink, Strategic, Normal)
- Comprehensive error handling and recovery mechanisms
- Memory-optimized data storage with size limits
- Automatic log and data file synchronization with Git
- Modular design for easy maintenance and updates
- Auto-backup system for data protection

## 💭 Technical Architecture

Raider V2 uses Selenium WebDriver to interact with web pages, extracting data from gaming platforms. The system is built with a multi-component architecture:

1. **OverlayDetector**: Identifies and handles overlays that might interfere with scraping operations
2. **DataManager**: Manages and validates extracted data before storing it
3. **GameDataExtractor**: Handles the core data extraction logic
4. **Raider**: Main class orchestrating the entire system
5. **GitSyncer**: Automatically uploads data and logs to git repository

## 🎈 Usage

```bash
python main.py --headless --debug
```

### Command Line Arguments:
- `--headless`: Run in headless mode (no visible browser)
- `--debug`: Enable debug output

## 🏁 Getting Started

### Prerequisites

- Python 3.6 or higher
- Chrome browser
- Git (for repository synchronization)

### Required Python packages:
```
selenium
rich
pandas
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/FIBA00/Raider_V2.git
cd Raider_V2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the system:
```bash
python main.py
```

## ⛏️ Built With

- [Selenium](https://www.selenium.dev/) - Web automation framework
- [Python](https://www.python.org/) - Programming language
- [Rich](https://rich.readthedocs.io/) - Terminal formatting and output
- [Git](https://git-scm.com/) - Version control and data synchronization

## 📋 Data Processing

The system collects data and categorizes it into three types:
1. **Pink Data** (values > 11.0)
2. **Strategic Data** (values between 2.0 and 10.0) 
3. **Normal Data** (all other values)

All data is saved in CSV format in the SDATA/Files directory, with regular backups to prevent data loss.

## 🔧 Maintenance Notes

### Regular Maintenance Tasks

1. **Update Selenium WebDriver**: Keep the WebDriver up-to-date with the latest Chrome version
2. **CSS Selector Updates**: If the target website structure changes, update selectors in `GameDataExtractor`
3. **Log Rotation**: Monitor log file size and rotate if necessary
4. **Database Maintenance**: Regularly check CSV files for corruption or issues
5. **Backup Verification**: Verify backup integrity periodically

### Troubleshooting

- **Connection Issues**: Check internet connectivity and target website status
- **Data Corruption**: Restore from backups in SDATA/Backups directory
- **Scraping Failures**: Check log files for specific error messages
- **Git Sync Failures**: Verify repository access and credentials

## 👨‍💻 Developer Information

The codebase follows these principles:

- **Type Annotations**: Full typing for better IDE support and error detection
- **Error Handling**: Comprehensive exception handling across all operations
- **Memory Management**: Systems to prevent memory leaks during long runs
- **Logging**: Multi-level logging with different verbosity levels
- **Modularity**: Component-based architecture for easier maintenance

### Future Development Plans

- AI-based anomaly detection for data patterns
- Web dashboard for real-time monitoring
- Support for additional data sources
- Parallel processing for increased speed

## ✍️ Authors

- **FIBA00** - Initial work and system design

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.


