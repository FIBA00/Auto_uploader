# Project Guide 
## About the project 
- this system is used for uploading any data from any source to a central git repository namely [GCloud_File_Storage].
- any repo can use this system to upload a file from any where such as termux , desktop and server also.
- we use personal access token for github api to access the repo then specific directory for given system and put the file in the repo.
* this system can be developed into a simple ctk desktop app or mobile app. and we can supply the token to the app and it will upload the file to the repo, 
* we can copy code inside the data forge system which is used for downloading csv datas from given repo, we can repurpose the methods that handle github interaction which is robust one. 


## How to use the system 
### 1. for models:
- this is used when we train our models in google colab and we want to upload the model to the repo.
* Token-based push to GitHub.
* Avoid using system `git` state (do not depend on local repo).
* **Push models to a specific repo** like `github.com/fraol/GCloud_File_Storage`.

#### ✅ Code Snippet for GitHub Upload via Token:

```python
import base64
import requests

def upload_file_to_github(token, repo, path_in_repo, file_path):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {"Authorization": f"token {token}"}
    
    data = {
        "message": f"Upload {path_in_repo}",
        "content": content,
        "branch": "main"
    }

    r = requests.put(url, headers=headers, json=data)
    print(f"Upload status: {r.status_code}, {r.text[:200]}")

# Example usage
# upload_file_to_github(MY_TOKEN, "fraol/models-repo", "models/model.pkl", "model.pkl")
```

#### ✅ Model Fetcher (script):
* this is specially used in the MPS where we dont have a api to interact with the  google colab cells directly so we can call this app through platform api.
* then the brain can check if the model needs training then calling this app then if the data is downloaded and placed in the needed path checking and triggering system restarts. 


```python
def download_file_from_github(token, repo, path_in_repo, output_path):
    url = f"https://raw.githubusercontent.com/{repo}/main/{path_in_repo}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)
    with open(output_path, 'wb') as f:
        f.write(r.content)
```

---

### 2. for uploading Scraper Output:
* Send the output of **phone or PC scraper** to a **common repo** (`GCloud_File_Storage`), accessible by all parts of MPS (desktop or mobile).
* we can use the same script for uploading the model to the repo.

* 🚀 What we Need:
    -  Token-based uploader
    -  Modular repo target (you pass `repo name`, `branch`, `folder`, etc.)
    -  Append/update logic (if daily file already exists → overwrite or append)

#### ✅ Generic Upload Script (Using GitHub API):

```python
def smart_upload_csv(token, repo, file_path, remote_path, commit_message="Upload new data"):
    import base64
    import requests

    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{remote_path}"
    headers = {"Authorization": f"token {token}"}

    # Check if file exists (to get SHA)
    resp = requests.get(url, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {
        "message": commit_message,
        "content": content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha  # required for updating

    res = requests.put(url, headers=headers, json=payload)
    print("Upload result:", res.status_code, res.text[:100])
```

> 🔁 This can be called as a **subprocess** from MPS or the mobile scraper:

```python
import subprocess
subprocess.run(["python", "upload_script.py", "--file", "daily.csv", "--repo", "fraol/GCloud_File_Storage"])
```

---

## 🔁 Connecting All 3 Systems:

1. **Scraper (PC and Phone)** writes CSVs daily to `data/`.
2. **Uploader (PC and Phone)** uses GitHub API to push to `fraol/scraper-central/data/YYYY-MM-DD.csv`.
3. **Trainer or MPS** downloads the files, processes, trains (if needed), and pushes new model or feedback to `fraol/models` repo.
4. **Mobile Client or another module** can pull updated `.pkl` model for inference.

---

## 🚀 Optional Additions:

* Use `.env` to store tokens securely, alternatively we can use the json based token and repo identification which data forge system uses. 
* Add daily cron/termux task for automation.
* Add GitHub Action to auto-train when data arrives (future automation idea).

---


## further implementation
---

### ✅ **1. Convert the Uploader to a CLI Tool**

Make it modular, argument-driven, and usable across Termux, Colab, or Desktop:

```bash
python auto_uploader.py --file daily.csv --repo fraol/GCloud_File_Storage --token $GH_TOKEN --path data/2025-07-08.csv --msg "Auto upload from mobile scraper"
```

Then define arguments using `argparse`:

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--msg", default="Auto upload")
    return parser.parse_args()
```

---

### ✅ **2. Integrate `.env` or `secrets.json` Support**

In Termux or servers, hardcoding tokens is risky. Add fallback logic to read from:

* `.env`:

```bash
GH_TOKEN=ghp_xxxxxxx
```

Use it in Python:

```python
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("GH_TOKEN")
```

* Or use a JSON config:

```json
{
  "token": "ghp_XXXXXX",
  "repo": "fraol/GCloud_File_Storage",
  "base_path": "models/"
}
```

---

### ✅ **3. Abstract Repo Logic (Support for Multiple Targets)**

Support uploads to:

* `models/` path
* `data/YYYY-MM-DD/` path
* `feedback/` folder (if needed for reports)

This gives MPS and DRS full control over where logic and signals go.

---

### ✅ **4. Add Timestamped Logging**

Simple upload log:

```python
from datetime import datetime

def log_upload(filename, status, msg):
    with open("upload_log.txt", "a") as log:
        log.write(f"{datetime.now()} | {filename} | {status} | {msg}\n")
```

---

### ✅ **5. Upload Mode Choices: Replace vs Append**

You could include a flag:

```bash
--mode overwrite     # default
--mode append        # if working with .txt/.csv and want to retain history
```

And add logic to:

* Pull the old file if exists
* Append new lines
* Push merged version

---

### ✅ **6. Consider a Watchdog Script (Optional for Future)**

A Termux/desktop daemon that watches a folder (`models/`, `output/`, `csvs/`) and when a new file is added, it auto-uploads.

---

### ✅ Final Structure Suggestion

```
auto_uploader/
│
├── uploader.py          # CLI + uploader engine
├── config.json          # fallback config (token, repo, branch, base_path)
├── .env                 # alternative for token storage
├── upload_log.txt       # saved logs
├── utils/
│   ├── github_api.py    # handles all PUTs, GETs, token header logic
│   └── file_utils.py    # handles base64, file read/write
```

---

### 🔁 Bonus: Reusable GitHub Uploader Class

You could eventually wrap the entire logic into a class:

```python
class GitHubUploader:
    def __init__(self, token, repo, branch='main'):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.headers = {"Authorization": f"token {token}"}

    def file_exists(self, path_in_repo):
        url = f"https://api.github.com/repos/{self.repo}/contents/{path_in_repo}"
        r = requests.get(url, headers=self.headers)
        return r.status_code == 200, r.json().get("sha") if r.ok else None

    def upload(self, file_path, path_in_repo, message):
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        exists, sha = self.file_exists(path_in_repo)
        payload = {
            "message": message,
            "content": content,
            "branch": self.branch
        }
        if sha: payload["sha"] = sha

        url = f"https://api.github.com/repos/{self.repo}/contents/{path_in_repo}"
        r = requests.put(url, headers=self.headers, json=payload)
        return r.status_code, r.text
```

---

Absolutely! Here’s a detailed analysis and feedback on your Project Guide for the Auto_uploader system:

---

## 1. **Project Purpose & Vision**
- **Clear Goal:** The guide makes it clear that the system is designed to upload data from any device (Termux, desktop, server, etc.) to a central GitHub repository, using token-based authentication.
- **Flexibility:** The vision to make it modular (CLI, desktop, or mobile app) and to support both uploading and downloading (fetching) is well-articulated.
- **Integration:** The idea to reuse robust code from the DataForge system for GitHub interactions is smart and efficient.

---

## 2. **How-To & Code Snippets**
- **Practical Examples:** The guide provides ready-to-use Python snippets for uploading and downloading files via the GitHub API, which is very helpful for users.
- **Token Security:** It emphasizes not relying on local git state and instead using the API directly, which is best practice for automation and cross-platform compatibility.

---

## 3. **Use Cases**
- **Model Uploads:** Clear instructions for uploading trained models from Colab or other environments.
- **Scraper Output:** Shows how to upload daily data from scrapers, making the system useful for data pipelines.
- **Subprocess Integration:** Demonstrates how the uploader can be called from other scripts or systems, increasing its utility.

---

## 4. **System Architecture & Flow**
- **End-to-End Flow:** The “Connecting All 3 Systems” section gives a concise overview of how scrapers, uploaders, trainers, and clients interact. This is great for onboarding new developers or users.
- **Automation Potential:** Mentions cron jobs, Termux tasks, and GitHub Actions for future automation, showing foresight.

---

## 5. **Implementation Suggestions**
- **CLI Tool:** Recommends making the uploader argument-driven and cross-platform, with a sample argparse implementation.
- **Config & Secrets:** Suggests using `.env` or JSON for token/config management, which is a security best practice.
- **Modular Repo Logic:** Encourages supporting multiple upload targets (models, data, feedback), making the tool adaptable.
- **Logging:** Proposes timestamped logging for uploads, which is essential for debugging and auditing.
- **Upload Modes:** Considers both overwrite and append modes for file uploads, which is important for data versioning.
- **Watchdog Script:** Suggests a daemon for auto-uploading on file changes—a nice touch for power users.

---

## 6. **Final Structure & Abstraction**
- **Directory Layout:** The proposed structure (with `uploader.py`, `config.json`, `.env`, `utils/`, etc.) is clean and scalable.
- **Reusable Class:** The GitHubUploader class abstraction is a solid foundation for maintainable and testable code.

---

## 7. **Overall Strengths**
- **Comprehensive:** Covers both high-level concepts and low-level implementation details.
- **User-Focused:** Anticipates real-world usage (mobile, desktop, automation).
- **Security-Aware:** Promotes best practices for token management.
- **Extensible:** Leaves room for future features (watchdog, GitHub Actions, etc.).

---

## 8. **Suggestions for Improvement**
- **Error Handling:** Consider adding more details or examples on handling API errors, rate limits, and retries.
- **Testing:** Suggest including a section on how to test uploads/downloads safely (e.g., using a test repo).
- **Permissions:** Briefly mention the required GitHub token scopes for uploads.
- **Dependencies:** List required Python packages (e.g., `requests`, `python-dotenv`) in the guide or a `requirements.txt`.
- **Security Note:** Remind users not to commit `.env` or `secrets.json` to public repos.

---

## 9. **Summary**
Your guide is well-structured, practical, and forward-thinking. It balances clarity for new users with enough technical depth for developers. With a few small additions (error handling, testing, security notes), it would be even stronger.

If you want, I can help you turn this into a README, generate a sample uploader CLI, or help with any of the “future” features you mentioned!