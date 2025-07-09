# standard project conventions 

## Project Structure
Project name/
│
├── main.py                  # Entry point (execution CLI/manager)
├── config/                  # Static config, tokens, constants
│   └── settings.py
│
├── core/                    # Core upload logic (engine + orchestrators)
│   ├── uploader.py          # Push logic
│   ├── validator.py         # File checks
│   └── router.py            # Path control logic
│
├── utils/                   # Shared helpers (not tied to core)
│   ├── logger.py
│   ├── file_ops.py
│   └── github_api.py
│
├── services/                # External integrations (APIs, etc.)
│   ├── drive_sync.py
│   └── github_hooks.py
│
└── tasks/                   # Optional: for CLI-task based separation
    ├── upload_local.py
    └── sync_all.py

## File Naming Conventions
| Type             | Pattern                    | Examples                            | Notes                   |
| ---------------- | -------------------------- | ----------------------------------- | ----------------------- |
| 🧠 Core logic    | `core/` + `<action>.py`    | `uploader.py`, `router.py`          | System internals        |
| 🛠 Utilities     | `utils/` + noun/verb combo | `file_ops.py`, `logger.py`          | Reusable across modules |
| 🔌 Services      | `services/` + provider/api | `github_api.py`, `drive_sync.py`    | External integrations   |
| 📦 Tasks/Scripts | `tasks/` + verb\_noun      | `upload_local.py`, `sync_models.py` | Good for CLI commands   |
| ⚙ Config         | `config/settings.py`       |                                     | Centralized constants   |



## git commit message conventions
| Type       | Description                              | Example                                               |
| ---------- | ---------------------------------------- | ----------------------------------------------------- |
| `feat`     | ✨ New feature                            | `feat(uploader): support multiple file types`         |
| `fix`      | 🐛 Bug fix                               | `fix(router): correct path resolution for edge cases` |
| `docs`     | 📚 Docs only                             | `docs(readme): add usage examples for sync`           |
| `style`    | 💅 Formatting (no code logic)            | `style(logger): fix spacing and add black format`     |
| `refactor` | 🔧 Code restructure (no new feature/bug) | `refactor(github_api): separate auth handler`         |
| `perf`     | ⚡ Performance improvement                | `perf(uploader): parallelize upload streams`          |
| `test`     | ✅ Add or fix tests                       | `test(uploader): mock GitHub API for dry-run`         |
| `build`    | 📦 Changes to build system/deps          | `build: update setup.py for pip publish`              |
| `ci`       | 🛠️ CI/CD config (GitHub Actions etc)    | `ci: fix release job branch filter`                   |
| `chore`    | 🔩 Maintenance, meta, no user impact     | `chore: cleanup .DS_Store and temp files`             |
| `revert`   | ⏪ Revert commit                          | `revert: feat(uploader) rollback bad patch`           |

## Concrete Ready-to-Use Set
|    Type      | Description                              |
|--------------|-----------------------
- feat:        | new feature
- fix:         | bug fix
- docs:        | documentation change
- style:       | formatting (no logic change)
- refactor:    | code refactor (no feature/bug)
- perf:        | performance improvement
- test:        | add or change test
- build:       | build tool or dependency change
- ci:          | CI/CD config change
- chore:       | non-code, housekeeping
- revert:      | revert previous commit
