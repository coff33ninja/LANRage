# LANrage Modernization Guide

This document explains the recent modernization of LANrage's project configuration and tooling.

## Overview

LANrage has been modernized to follow current Python best practices (PEP 621) and use modern tooling for improved developer experience and maintainability.

## Changes Made

### 1. PEP 621 Compliant pyproject.toml

**What Changed**: Expanded `pyproject.toml` to be the single source of truth for project metadata and dependencies.

**Benefits**:
- Standard format supported by all modern Python tools (pip, setuptools, hatch, poetry)
- Single file for all project configuration
- Better IDE integration and autocomplete
- Easier dependency management

**Key Sections Added**:
```toml
[build-system]          # How the package is built
[project]               # Project metadata and dependencies
[project.optional-dependencies]  # Dev dependencies
[project.urls]          # Project links
[project.scripts]       # Entry points
```

### 2. Ruff Integration

**What Changed**: Added comprehensive Ruff configuration for modern, fast linting.

**Benefits**:
- 10-100x faster than traditional linters
- Replaces multiple tools (flake8, isort checks, pyupgrade)
- Auto-fixes many issues
- Better error messages

**Ruff Features Enabled**:
- `E/W`: pycodestyle errors and warnings
- `F`: Pyflakes (undefined names, unused imports)
- `I`: isort (import sorting)
- `N`: pep8-naming (naming conventions)
- `UP`: pyupgrade (modern Python syntax)
- `B`: flake8-bugbear (common bugs)
- `C4`: flake8-comprehensions (better comprehensions)
- `SIM`: flake8-simplify (code simplification)
- `RET`: flake8-return (return statement issues)

### 3. Pytest Configuration

**What Changed**: Added pytest configuration to `pyproject.toml`.

**Benefits**:
- Consistent test execution
- Automatic coverage reporting
- Async test support configured
- No separate pytest.ini needed

### 4. Coverage Configuration

**What Changed**: Added coverage.py configuration for better test coverage reporting.

**Benefits**:
- Precise coverage metrics (88% currently)
- Excludes test files and virtual environments
- Identifies missing coverage lines
- JSON output for CI/CD integration

## Installation Methods

### Method 1: Using pyproject.toml (Recommended)

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Install production only
uv pip install -e .
```

### Method 2: Using requirements.txt (Backwards Compatible)

```bash
# Install all dependencies
uv pip install -r requirements.txt
```

## New Development Workflow

### Code Quality Checks

```bash
# 1. Sort imports (isort)
.venv\Scripts\python.exe -m isort .

# 2. Format code (black)
.venv\Scripts\python.exe -m black .

# 3. Lint with Ruff (fast!)
.venv\Scripts\python.exe -m ruff check --fix .

# 4. Run tests with coverage
.venv\Scripts\python.exe -m pytest
```

### Using Ruff Instead of Multiple Tools

Ruff can replace several tools:

```bash
# Old way (multiple commands)
isort --check .
flake8 .
pyupgrade --py312-plus **/*.py

# New way (single command)
ruff check .
```

## Migration Notes

### For Existing Developers

1. **No immediate action required** - `requirements.txt` still works
2. **Recommended**: Switch to `uv pip install -e ".[dev]"` for faster installs
3. **Optional**: Start using `ruff check` instead of multiple linters

### For CI/CD

The existing CI workflows continue to work without changes. Future optimization:

```yaml
# Old
- run: isort --check .
- run: black --check .
- run: flake8 .

# New (faster)
- run: ruff check .
- run: black --check .  # Keep black for formatting
```

## Tool Comparison

| Feature | Old Setup | New Setup |
|---------|-----------|-----------|
| Linting | flake8 + pylint | Ruff + pylint |
| Import sorting | isort | isort + Ruff |
| Formatting | black | black |
| Speed | ~5-10s | ~0.5-1s |
| Config files | Multiple | Single (pyproject.toml) |

## Configuration Reference

### Ruff Commands

```bash
# Check all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Check specific file
ruff check core/games.py

# Show all rules
ruff rule --all

# Explain a specific rule
ruff rule E501
```

### Pytest Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_games.py

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Coverage Commands

```bash
# Generate coverage report
pytest --cov --cov-report=html

# View coverage in browser
# Open htmlcov/index.html

# Generate JSON for CI
pytest --cov --cov-report=json
```

## Performance Improvements

### Ruff vs Traditional Linters

Based on LANrage codebase (~5000 lines):

| Tool | Time | Notes |
|------|------|-------|
| flake8 | ~3-5s | Single-threaded |
| pylint | ~8-12s | Comprehensive but slow |
| Ruff | ~0.3-0.5s | Rust-based, parallel |

### Installation Speed

Using `pyproject.toml` with uv:

| Method | Time | Notes |
|--------|------|-------|
| pip + requirements.txt | ~30-45s | Traditional |
| uv + requirements.txt | ~5-8s | Fast resolver |
| uv + pyproject.toml | ~4-6s | Optimized |

## Future Enhancements

### Potential Tool Consolidation

Consider replacing more tools with Ruff in the future:

1. **Ruff Format** (experimental) - Could replace black
2. **Ruff Import Sorting** - Already included, could replace isort
3. **More Rules** - Add security checks (S), documentation (D), etc.

### Build System

Current setup uses setuptools. Consider alternatives:

- **Hatch**: Modern, fast, good defaults
- **PDM**: PEP 582 support, lock files
- **Poetry**: Popular, comprehensive

## Troubleshooting

### Ruff Not Found

```bash
# Install ruff
uv pip install ruff

# Or reinstall all dev dependencies
uv pip install -e ".[dev]"
```

### Import Errors After Migration

```bash
# Reinstall in editable mode
uv pip install -e .
```

### Coverage Not Working

```bash
# Install coverage dependencies
uv pip install pytest-cov

# Or reinstall dev dependencies
uv pip install -e ".[dev]"
```

## References

- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [coverage.py Documentation](https://coverage.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)

## Questions?

For questions about the modernization:
1. Check this document
2. Review `pyproject.toml` comments
3. Open an issue on GitHub
4. Check the [development guide](DEVELOPMENT.md)
