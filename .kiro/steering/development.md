# LANrage Development Environment

## Required Tools

- **Python 3.12+** (required, no exceptions)
- **uv** - Modern Python package manager
- **Virtual environment** - Always use `.venv`

## Initial Setup

### 1. Install uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/lanrage.git
cd lanrage

# Run automated setup
python setup.py
```

The setup script will:
- Verify Python 3.12+
- Create `.venv` virtual environment
- Install all dependencies via uv
- Create `.env` from `.env.example`

### 3. Activate Virtual Environment

```bash
# Windows
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

## Manual Setup (if setup.py fails)

```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate it
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
uv pip install -r requirements.txt

# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

## Code Quality Setup

### Install Development Tools

```bash
# Activate venv first
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Install code quality tools (already in requirements.txt)
uv pip install -r requirements.txt
```

### Code Quality Tools

The project uses three main code quality tools:

1. **isort** - Organizes and sorts imports alphabetically
2. **black** - Opinionated code formatter for consistent style
3. **ruff** - Fast Python linter for catching errors and style issues

### Run Code Quality Checks

```bash
# Always use venv Python for consistency

# 1. Sort imports with isort
.venv\Scripts\python.exe -m isort .  # Windows
.venv/bin/python -m isort .          # Linux/Mac

# 2. Format code with Black
.venv\Scripts\python.exe -m black .  # Windows
.venv/bin/python -m black .          # Linux/Mac

# 3. Lint with Ruff
.venv\Scripts\python.exe -m ruff check .  # Windows
.venv/bin/python -m ruff check .          # Linux/Mac

# 4. Fix auto-fixable issues
.venv\Scripts\python.exe -m ruff check --fix .  # Windows
.venv/bin/python -m ruff check --fix .          # Linux/Mac

# 5. Run tests
.venv\Scripts\python.exe -m pytest tests/  # Windows
.venv/bin/python -m pytest tests/          # Linux/Mac
```

### Check-Only Mode (CI/CD)

```bash
# Check imports without modifying
.venv\Scripts\python.exe -m isort --check-only .  # Windows
.venv/bin/python -m isort --check-only .          # Linux/Mac

# Check formatting without modifying
.venv\Scripts\python.exe -m black --check .  # Windows
.venv/bin/python -m black --check .          # Linux/Mac

# Lint without fixing
.venv\Scripts\python.exe -m ruff check .  # Windows
.venv/bin/python -m ruff check .          # Linux/Mac
```

### Pre-commit Setup (Recommended)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

Install pre-commit:

```bash
uv pip install pre-commit
pre-commit install
```

## Daily Workflow

### Starting Work

```bash
# 1. Activate virtual environment
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# 2. Update dependencies (if needed)
uv pip install -r requirements.txt

# 3. Run LANrage
python lanrage.py
```

### Before Committing

```bash
# Always use venv Python

# 1. Sort imports
.venv\Scripts\python.exe -m isort .  # Windows
.venv/bin/python -m isort .          # Linux/Mac

# 2. Format code
.venv\Scripts\python.exe -m black .  # Windows
.venv/bin/python -m black .          # Linux/Mac

# 3. Lint and fix
.venv\Scripts\python.exe -m ruff check --fix .  # Windows
.venv/bin/python -m ruff check --fix .          # Linux/Mac

# 4. Run tests
.venv\Scripts\python.exe -m pytest tests/  # Windows
.venv/bin/python -m pytest tests/          # Linux/Mac

# 5. Commit if all pass
git add .
git commit -m "your message"
```

## Adding Dependencies

### Always use uv

```bash
# Add a new package
uv pip install package-name

# Update requirements.txt
uv pip freeze > requirements.txt

# Or manually add to requirements.txt and install
echo "package-name>=1.0.0" >> requirements.txt
uv pip install -r requirements.txt
```

### Never use pip directly

❌ Bad:
```bash
pip install package-name
```

✅ Good:
```bash
uv pip install package-name
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Delete and recreate venv
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows

# Recreate with uv
uv venv --python 3.12
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac
uv pip install -r requirements.txt
```

### Python Version Issues

```bash
# Check Python version
python --version  # Must be 3.12+

# If wrong version, specify explicitly
uv venv --python 3.12
# or
uv venv --python /path/to/python3.12
```

### uv Not Found

```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Or via pip
pip install uv
```

## Quick Reference

```bash
# Setup (one-time)
python setup.py

# Activate venv (recommended)
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Or use venv directly without activation
.venv\Scripts\python.exe script.py  # Windows
.venv/bin/python script.py          # Linux/Mac

# Run LANrage (with venv)
.venv\Scripts\python.exe lanrage.py  # Windows
.venv/bin/python lanrage.py          # Linux/Mac

# Code quality (always use venv python)
.venv\Scripts\python.exe -m isort .              # Sort imports
.venv\Scripts\python.exe -m black .              # Format
.venv\Scripts\python.exe -m ruff check --fix .   # Lint
.venv\Scripts\python.exe -m pytest tests/        # Test

# Add dependency (activate venv first)
uv pip install package-name
uv pip freeze > requirements.txt
```

## IDE Configuration

### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/Mac)
4. Enable Black formatter in Settings → Tools → Black
5. Enable Ruff in Settings → Tools → External Tools

## Environment Variables

Edit `.env` file for configuration:

```bash
# Mode: client or relay
LANRAGE_MODE=client

# API settings
LANRAGE_API_HOST=127.0.0.1
LANRAGE_API_PORT=8666

# Relay settings (for relay mode)
LANRAGE_RELAY_IP=your.public.ip
```

## Virtual Environment Detection

**ALWAYS DETECT AND USE VENV BEFORE RUNNING SCRIPTS OR TESTS**

Before executing any Python scripts, tests, or commands:

1. Check if `.venv` exists
2. Use the venv Python interpreter if available
3. Warn if venv is not activated

### Automatic Detection Pattern

```bash
# Windows
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe script.py
) else (
    python script.py
)

# Linux/Mac
if [ -f .venv/bin/python ]; then
    .venv/bin/python script.py
else
    python script.py
fi
```

### Running Commands with Venv

```bash
# Always prefer venv Python
.venv\Scripts\python.exe lanrage.py  # Windows
.venv/bin/python lanrage.py          # Linux/Mac

# Or activate first
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac
python lanrage.py
```

## Running Tests

**Always use venv Python for tests:**

```bash
# All tests (with venv)
.venv\Scripts\python.exe -m pytest tests/  # Windows
.venv/bin/python -m pytest tests/          # Linux/Mac

# Or activate venv first
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Then run tests
pytest tests/

# Specific test file
pytest tests/test_nat.py

# With coverage
pytest --cov=core --cov=api tests/

# Verbose output
pytest -v tests/

# Stop on first failure
pytest -x tests/
```

## Documentation

When adding new features, update:
- Code docstrings (required)
- `docs/` markdown files (if architecture changes)
- `README.md` (if user-facing changes)
- Tests in `tests/` (always)
