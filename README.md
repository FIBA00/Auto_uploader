# Auto_uploader

## About the Project

Auto_uploader is a flexible system for uploading any data (models, CSVs, etc.) from any device (Termux, desktop, server, Colab) to a central GitHub repository (e.g., `GCloud_File_Storage`). It uses GitHub API token authentication and does not depend on local git state. The system is modular and can be used as a CLI tool, integrated into scripts, or extended into desktop/mobile apps.

- Upload files from anywhere to a central repo
- Token-based authentication (no git state required)
- Modular: CLI, script, or future GUI/mobile
- Can be used for model uploads, scraper outputs, or any file

---

## Table of Contents
- [About](#about)
- [How to Use](#how-to-use)
- [Architecture](#architecture)
- [Implementation](#implementation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Suggestions & Best Practices](#suggestions--best-practices)
- [Authors](#authors)

---

## How to Use

### CLI Usage Example

```bash
python auto_uploader.py --file daily.csv --repo fraol/GCloud_File_Storage --token $GH_TOKEN --path data/2025-07-08.csv --msg "Auto upload from mobile scraper"
```

---

## Architecture

1. **Scraper (PC/Phone)** writes CSVs to `data/`.
2. **Uploader** uses GitHub API to push to `fraol/scraper-central/data/YYYY-MM-DD.csv`.
3. **Trainer/MPS** downloads files, processes, trains, and pushes new models or feedback.
4. **Clients** can pull updated models for inference.

---

## Implementation

- **Token-based uploads** (no git state)
- **Modular repo/branch/folder targeting**
- **Overwrite or append logic for files**
- **Logging of uploads**
- **Configurable via CLI, `.env`, or JSON**


## Configuration

- Store tokens in `.env` or `config.json` (do not hardcode in scripts)
- Example `.env`:
  ```env
  GH_TOKEN=ghp_xxxxxxx
  ```
- Example `config.json`:
  ```json
  {
    "token": "ghp_XXXXXX",
    "repo": "fraol/GCloud_File_Storage",
    "base_path": "models/"
  }
  ```
- Use `python-dotenv` to load `.env` in Python:
  ```python
  from dotenv import load_dotenv
  import os
  load_dotenv()
  token = os.getenv("GH_TOKEN")
  ```

---

## Project Structure

```
auto_uploader/
├── uploader.py          # CLI + uploader engine
├── config.json          # fallback config (token, repo, branch, base_path)
├── .env                 # alternative for token storage
├── upload_log.txt       # saved logs
├── utils/
│   ├── github_api.py    # handles all PUTs, GETs, token header logic
│   └── file_utils.py    # handles base64, file read/write
```

---


## Authors
- [@fraold](https://github.com/fraold) - Project lead

---

## Acknowledgements
- Inspired by robust data pipeline and automation needs
- Thanks to contributors and open-source libraries
