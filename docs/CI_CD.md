# CI/CD Pipeline Documentation

## Overview

LANrage uses GitHub Actions for code quality, test execution, automated version tagging, release publishing, and documentation sync.

## Active Workflows

### 1. Main CI (`.github/workflows/ci.yml`)

**Triggers**
- Push to `main` and `develop`
- Pull requests to `main` and `develop`

**Jobs**
- `code-quality`
  - `isort --check-only`
  - `black --check`
  - `ruff check` (strict)
- `test` (matrix)
  - OS: `ubuntu-latest`, `windows-latest`
  - Python: `3.12`, `3.13`
  - Coverage artifact upload on Linux + Python 3.12
- `security`
  - `safety` vulnerability scan
  - `bandit` static security scan

## Release and Version Automation

### 2. Auto Tag (`.github/workflows/auto-tag.yml`)

**Purpose**
- Creates and pushes a git tag (`vX.Y.Z`) when `pyproject.toml` version changes on `main`.

**Trigger**
- Push to `main` affecting `pyproject.toml`
- Manual dispatch

### 3. Release (`.github/workflows/release.yml`)

**Purpose**
- Creates GitHub Releases from tags and generates release notes automatically.

**Triggers**
- Push tags matching `v*.*.*`
- Manual dispatch with `tag_name`

**Key behavior**
- Extracts version from tag
- Uses `softprops/action-gh-release`
- `generate_release_notes: true`
- Builds source distribution and uploads `dist/*` assets

### 4. README Version Sync (`.github/workflows/update-readme-version.yml`)

**Purpose**
- Keeps README version badge/status aligned with the project version.

**Triggers**
- Push to `main`
- Tag push `v*.*.*`
- Manual dispatch

### 5. Supported Games Sync (`.github/workflows/update-supported-games-readme.yml`)

**Purpose**
- Regenerates supported-games documentation from JSON profile data.

**Triggers**
- Push to `main` when:
  - `game_profiles/**/*.json` changes
  - `tools/update_supported_games_readme.py` changes
  - `README.md` changes
- Manual dispatch

**Outputs**
- Updates `README.md` supported games block
- Updates `docs/SUPPORTED_GAMES.md`

### 6. Ruff Workflow (`.github/workflows/ruff.yml`)

Runs standalone Ruff checks for lint-focused validation.

### 7. Pylint Workflow (`.github/workflows/pylint.yml`)

Runs Pylint analysis as an additional quality gate.

## Local Commands (Match CI)

```bash
# Linux/macOS
source .venv/bin/activate
python -m isort --check-only --diff .
python -m black --check --diff .
python -m ruff check .
python -m pytest tests/ -v
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
python -m isort --check-only --diff .
python -m black --check --diff .
python -m ruff check .
python -m pytest tests/ -v
```

## Notes

- `CHANGELOG.md` remains the manual source of truth for curated release notes.
- GitHub auto-generated release notes are enabled in release workflow.
- README and supported-games docs are auto-synced by CI workflows.

---

**Last Updated**: February 22, 2026
