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

