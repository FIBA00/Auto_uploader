import argparse
import os
import json
import base64
import requests
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from utils.logger import get_logger

logger = get_logger(__file__)



CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'upload_log.txt')

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

    def download_file(self, path_in_repo, local_path):
        url = f"https://raw.githubusercontent.com/{self.repo}/{self.branch}/{path_in_repo}"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(r.content)
            return True
        return False

    def upload(self, file_path, path_in_repo, message, mode='overwrite'):
        # For append mode, download, merge, and re-upload
        if mode == 'append':
            exists, _ = self.file_exists(path_in_repo)
            if exists:
                # Download old file
                tmp_path = file_path + '.tmp_old'
                if self.download_file(path_in_repo, tmp_path):
                    with open(tmp_path, 'rb') as f_old, open(file_path, 'rb') as f_new:
                        merged = f_old.read() + b"\n" + f_new.read()
                    with open(file_path, 'wb') as f:
                        f.write(merged)
                    os.remove(tmp_path)
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        exists, sha = self.file_exists(path_in_repo)
        payload = {
            "message": message,
            "content": content,
            "branch": self.branch
        }
        if sha:
            payload["sha"] = sha
        url = f"https://api.github.com/repos/{self.repo}/contents/{path_in_repo}"
        r = requests.put(url, headers=self.headers, json=payload)
        return r.status_code, r.text

def log_upload(filename, status, msg):
    with open(LOG_PATH, "a") as log:
        log.write(f"{datetime.now()} | {filename} | {status} | {msg}\n")

def load_config():
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    return config

def main():
    parser = argparse.ArgumentParser(description="Upload files to GitHub via API.")
    parser.add_argument("--file", required=True, help="Local file to upload")
    parser.add_argument("--repo", help="GitHub repo (e.g. user/repo)")
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--path", required=True, help="Path in repo to upload to")
    parser.add_argument("--msg", default="Auto upload", help="Commit message")
    parser.add_argument("--mode", choices=["overwrite", "append"], default="overwrite", help="Upload mode")
    parser.add_argument("--branch", default="main", help="Target branch")
    args = parser.parse_args()

    config = load_config()
    token = args.token or os.getenv("GH_TOKEN") or config.get("token")
    repo = args.repo or config.get("repo")
    branch = args.branch or config.get("branch", "main")
    if not token or not repo:
        logger.info("Error: GitHub token and repo must be provided via args, .env, or config.json")
        exit(1)

    uploader = GitHubUploader(token, repo, branch)
    status, resp = uploader.upload(args.file, args.path, args.msg, mode=args.mode)
    logger.info(f"Upload status: {status}\n{resp[:200]}")
    log_upload(args.file, status, args.msg)

if __name__ == "__main__":
    main()
