# CI/CD Pipeline Documentation

## Overview

LANrage uses GitHub Actions for continuous integration and deployment. The pipeline ensures code quality, runs comprehensive tests, and automates releases.

## Workflows

### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

**Triggers**: Push to `main`/`develop`, Pull Requests

**Jobs**:

#### Code Quality
- **Import Sorting**: Verifies imports are sorted with isort
- **Code Formatting**: Checks Black formatting compliance
- **Ruff Linting**: Strict mode - zero tolerance for warnings
- **Zero Warnings Check**: Enforces 100% Ruff compliance

#### Test Suite
- **Matrix Testing**: Python 3.12 & 3.13 on Ubuntu & Windows
- **Coverage**: 88% target (measured on Python 3.12/Ubuntu)
- **Test Count**: 375 tests across 24 test files
- **Artifacts**: Coverage reports uploaded for analysis

#### Security Scan
- **Vulnerability Check**: Safety checks for known CVEs
- **Security Linting**: Bandit scans for security issues
- **Reports**: JSON reports uploaded as artifacts

### 2. Ruff Code Quality (`.github/workflows/ruff.yml`)

**Triggers**: Push, Pull Requests, Manual dispatch

**Jobs**:

#### Ruff Check
- **Linting**: Comprehensive Ruff analysis with statistics
- **Strict Mode**: Fails on any warnings (100% compliance required)
- **GitHub Integration**: Annotations on PR diffs
- **Report Generation**: JSON report for detailed analysis

#### Ruff Format Check (Experimental)
- **Format Compatibility**: Checks Ruff formatter vs Black
- **Non-blocking**: Informational only, doesn't fail build
- **Future-proofing**: Prepares for potential Black → Ruff migration

#### Code Quality Summary
- **Status Report**: Aggregates all check results
- **Pass/Fail**: Clear indication of code quality status
- **Guidance**: Provides fix commands on failure

### 3. Pylint Analysis (`.github/workflows/pylint.yml`)

**Triggers**: Push, Pull Requests, Manual dispatch

**Jobs**:

#### Pylint Analysis
- **Matrix**: Python 3.12 & 3.13
- **Scoring**: Tracks code quality score (target: 9.0+/10.0)
- **Reports**: JSON reports per Python version
- **Colorized Output**: Easy-to-read console output

### 4. Release Automation (`.github/workflows/release.yml`)

**Triggers**: Tag push (`v*`)

**Jobs**:

#### Create Release
- **Changelog Extraction**: Auto-extracts version notes
- **Asset Building**: Creates distribution packages
- **GitHub Release**: Publishes release with notes
- **Permissions**: Requires `contents: write`

## Code Quality Standards

### Ruff Configuration

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "RET",  # flake8-return
]
```

### Quality Gates

| Check | Tool | Threshold | Status |
|-------|------|-----------|--------|
| Linting | Ruff | Zero warnings | ✅ 100% |
| Formatting | Black | 100% compliant | ✅ Pass |
| Import Sorting | isort | 100% compliant | ✅ Pass |
| Test Coverage | pytest-cov | 85%+ | ✅ 88% |
| Pylint Score | pylint | 9.0+/10.0 | ✅ 10.0 |
| Security | Bandit | No high issues | ✅ Pass |

## Running Checks Locally

### Quick Check (Pre-commit)
```bash
# Windows
.venv\Scripts\python.exe -m isort .
.venv\Scripts\python.exe -m black .
.venv\Scripts\python.exe -m ruff check --fix .
.venv\Scripts\python.exe -m pytest tests/

# Linux/Mac
.venv/bin/python -m isort .
.venv/bin/python -m black .
.venv/bin/python -m ruff check --fix .
.venv/bin/python -m pytest tests/
```

### Full CI Simulation
```bash
# Code quality
python -m isort --check-only --diff .
python -m black --check --diff .
python -m ruff check . --output-format=github

# Tests with coverage
python -m pytest tests/ -v --cov=core --cov=api --cov-report=term

# Pylint analysis
pylint $(git ls-files '*.py') --score=yes

# Security scan
safety check
bandit -r core/ api/ servers/
```

## Workflow Status Badges

Add to README.md:

```markdown
![CI](https://github.com/coff33ninja/LANRage/workflows/CI/badge.svg)
![Ruff](https://github.com/coff33ninja/LANRage/workflows/Ruff%20Code%20Quality/badge.svg)
![Pylint](https://github.com/coff33ninja/LANRage/workflows/Pylint/badge.svg)
```

## Troubleshooting

### Ruff Failures

**Issue**: Ruff check fails in CI but passes locally

**Solution**:
```bash
# Ensure you're using the same Ruff version
pip show ruff

# Update to latest
uv pip install --upgrade ruff

# Run with same output format as CI
python -m ruff check . --output-format=github
```

### Test Failures

**Issue**: Tests pass locally but fail in CI

**Common Causes**:
1. **Platform differences**: Windows vs Linux path separators
2. **Missing dependencies**: Check requirements.txt
3. **Environment variables**: Verify .env configuration
4. **Timing issues**: Async tests may be flaky

**Solution**:
```bash
# Run tests in verbose mode
pytest tests/ -v --tb=long

# Check for platform-specific issues
pytest tests/ -v -k "not windows" # On Linux
pytest tests/ -v -k "not linux"   # On Windows
```

### Coverage Drops

**Issue**: Coverage below 85% threshold

**Solution**:
```bash
# Generate detailed coverage report
pytest --cov=core --cov=api --cov-report=html

# Open htmlcov/index.html to see uncovered lines
# Add tests for uncovered code paths
```

## Performance

### CI Pipeline Timing

| Job | Duration | Notes |
|-----|----------|-------|
| Code Quality | ~2 min | Ruff is very fast |
| Test Suite (Ubuntu) | ~3 min | 375 tests |
| Test Suite (Windows) | ~4 min | Slightly slower |
| Security Scan | ~2 min | Includes downloads |
| **Total** | **~5-7 min** | Parallel execution |

### Optimization Tips

1. **Cache Dependencies**: uv is already fast, but consider caching `.venv`
2. **Parallel Tests**: Use `pytest -n auto` for parallel execution
3. **Selective Testing**: Use `pytest -k` for targeted test runs
4. **Skip Slow Tests**: Mark slow tests with `@pytest.mark.slow`

## Future Improvements

### Planned Enhancements

1. **Ruff Format Migration**: Replace Black with Ruff's formatter
2. **Pre-commit Hooks**: Auto-run checks before commit
3. **Codecov Integration**: Better coverage tracking and visualization
4. **Dependabot**: Automated dependency updates
5. **Performance Benchmarks**: Track performance regressions
6. **Docker CI**: Test in containerized environments

### Experimental Features

1. **Ruff Format**: Currently in experimental check mode
2. **Python 3.13**: Testing compatibility with latest Python
3. **Matrix Expansion**: Consider macOS testing

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [LANrage Testing Guide](./TESTING.md)
- [LANrage Ruff Migration](./RUFF_MIGRATION.md)

## Support

For CI/CD issues:
1. Check workflow logs in GitHub Actions tab
2. Review this documentation
3. Run checks locally to reproduce
4. Open an issue with workflow run link

---

**Last Updated**: January 30, 2026  
**Maintained By**: LANrage Development Team
