# LANrage Code Quality Rules

## Code Preservation & Removal Rules

### Import Management

**NEVER REMOVE AN IMPORT** - Always find a way to use it. If an import exists, it's there for a reason.

- If you see an unused import, investigate why it was added
- Find a legitimate use case for the import in the code
- If truly unnecessary, comment it out with explanation rather than deleting
- Consider that imports may be used for type hints, side effects, or future functionality

### Code Removal Decision Process

**ALWAYS INVESTIGATE BEFORE REMOVING** - When you find duplicate or seemingly unnecessary code:

1. **Analyze the context:**
   - Why might this code exist?
   - Is it a duplicate (bug) or intentional (future use)?
   - What was the original developer's intent?

2. **Check for patterns:**
   - Look for similar patterns in the codebase
   - Check if it's part of a larger design pattern
   - Verify if it's dead code or planned functionality

3. **Document your reasoning:**
   - If removing: explain WHY it was wrong/duplicate
   - If keeping: explain the purpose
   - Add comments for future developers

**Example - Duplicate Code (Correct to Remove):**
```python
# BEFORE (Bug - duplicate registration)
try:
    transport, protocol = await loop.create_datagram_endpoint(...)
    self.listeners[port] = transport  # ✅ Correct registration
    logger.info(f"Listener started on port {port}")
except Exception as e:
    sock.close()
    raise

self.listeners[port] = transport  # ❌ Duplicate - unreachable if exception

# AFTER (Fixed)
try:
    transport, protocol = await loop.create_datagram_endpoint(...)
    self.listeners[port] = transport  # ✅ Single registration
    logger.info(f"Listener started on port {port}")
except Exception as e:
    sock.close()
    raise
# Removed duplicate - it was unreachable and redundant
```

**Example - Planned Code (Keep with Comment):**
```python
# Unused import that might be needed later
# from .advanced_nat import SymmetricNATHandler  # TODO: Implement symmetric NAT support

# Placeholder for future feature
# async def handle_symmetric_nat(self):
#     """Handle symmetric NAT traversal - planned for v2.0"""
#     pass
```

**When in doubt:**
- Ask the user before removing
- Comment out instead of deleting
- Document your uncertainty

## Exception Handling

**ALL EXCEPTIONS MUST BE VALIDATED WITH PROPER LOGIC**

Bad:
```python
try:
    result = risky_operation()
except Exception as e:
    pass  # ❌ Silent failure
```

Good:
```python
try:
    result = risky_operation()
except ValueError as e:
    # ✅ Specific exception with validation
    if "expected error pattern" in str(e):
        logger.warning(f"Known issue occurred: {e}")
        return default_value
    raise  # Re-raise unexpected errors
except Exception as e:
    # ✅ Log and handle appropriately
    logger.error(f"Unexpected error in risky_operation: {e}")
    raise NetworkError(f"Operation failed: {e}") from e
```

Requirements:
- Use specific exception types when possible
- Always validate the exception content
- Log exceptions with context
- Never silently swallow exceptions without validation
- Re-raise or convert to domain-specific exceptions when appropriate

## F-String Formatting

**F-STRINGS ALWAYS NEED PLACEHOLDERS**

Bad:
```python
message = f"Operation completed"  # ❌ No placeholder, use regular string
error = f"Failed"  # ❌ No placeholder
```

Good:
```python
message = "Operation completed"  # ✅ Regular string when no interpolation
error = f"Failed: {operation_name}"  # ✅ Has placeholder
status = f"Peer {peer_id} connected with {latency_ms}ms latency"  # ✅ Multiple placeholders
```

Requirements:
- Only use f-strings when you have variables to interpolate
- Use regular strings for static messages
- Always include at least one `{variable}` placeholder in f-strings
- Prefer f-strings over `.format()` or `%` formatting when interpolating

## Additional Quality Standards

### Logging
- Use appropriate log levels (debug, info, warning, error)
- Include context in log messages
- Log exceptions with full traceback when appropriate

### Type Hints
- Required for all function signatures
- Use `Optional[T]` for nullable types
- Use `list[T]`, `dict[K, V]` modern syntax

### Docstrings
- Required for all public functions and classes
- Include Args, Returns, and Raises sections
- Keep them concise but informative

### Error Messages
- Be specific about what went wrong
- Include relevant context (file paths, IPs, etc.)
- Suggest solutions when possible

## Code Quality Tools

LANrage uses **four main tools** configured in `pyproject.toml` (PEP 621):

### 1. isort - Import Organization

Automatically sorts and organizes imports alphabetically and by type (standard library, third-party, local).
Configured with `profile = "black"` for compatibility.

```bash
# Sort imports (use venv Python)
.venv\Scripts\python.exe -m isort .  # Windows
.venv/bin/python -m isort .          # Linux/Mac

# Check without modifying
.venv\Scripts\python.exe -m isort --check-only .  # Windows
.venv/bin/python -m isort --check-only .          # Linux/Mac
```

### 2. black - Code Formatting

Opinionated code formatter that ensures consistent style across the codebase.
Line length: 88, Target: Python 3.12+

```bash
# Format code (use venv Python)
.venv\Scripts\python.exe -m black .  # Windows
.venv/bin/python -m black .          # Linux/Mac

# Check without modifying
.venv\Scripts\python.exe -m black --check .  # Windows
.venv/bin/python -m black --check .          # Linux/Mac
```

### 3. ruff - Fast Linting

Fast Python linter that replaces flake8, pyupgrade, and more.
**9 rule categories enabled**: E (pycodestyle errors), F (Pyflakes), I (isort), N (pep8-naming), 
W (pycodestyle warnings), UP (pyupgrade), B (flake8-bugbear), C4 (flake8-comprehensions), 
SIM (flake8-simplify), RET (flake8-return)

```bash
# Lint code (use venv Python)
.venv\Scripts\python.exe -m ruff check .  # Windows
.venv/bin/python -m ruff check .          # Linux/Mac

# Fix auto-fixable issues
.venv\Scripts\python.exe -m ruff check --fix .  # Windows
.venv/bin/python -m ruff check --fix .          # Linux/Mac
```

### 4. pylint - Static Analysis

Additional static analysis for catching complex issues.
Current score: **10.00/10** (perfect)

```bash
# Run pylint (use venv Python)
.venv\Scripts\python.exe -m pylint core/ api/ servers/  # Windows
.venv/bin/python -m pylint core/ api/ servers/          # Linux/Mac
```

## Pre-Commit Workflow

Always run these commands before committing (in order):

```bash
# 1. Sort imports
.venv\Scripts\python.exe -m isort .  # Windows
.venv/bin/python -m isort .          # Linux/Mac

# 2. Format code
.venv\Scripts\python.exe -m black .  # Windows
.venv/bin/python -m black .          # Linux/Mac

# 3. Lint and fix
.venv\Scripts\python.exe -m ruff check --fix .  # Windows
.venv/bin/python -m ruff check --fix .          # Linux/Mac

# 4. Static analysis
.venv\Scripts\python.exe -m pylint core/ api/ servers/  # Windows
.venv/bin/python -m pylint core/ api/ servers/          # Linux/Mac

# 5. Run tests
.venv\Scripts\python.exe -m pytest tests/  # Windows
.venv/bin/python -m pytest tests/          # Linux/Mac
```

All commands must pass before committing code (CI/CD enforced).

## Installation

All code quality tools are in `pyproject.toml` dev dependencies:

```bash
# Install all dependencies including dev tools
uv pip install -e ".[dev]"

# Or use requirements.txt (backwards compatibility)
uv pip install -r requirements.txt
```

Tools included:
- `black>=23.3.0` - Code formatter
- `isort>=5.12.0` - Import sorter
- `ruff>=0.1.0` - Fast linter (replaces flake8, pyupgrade, etc.)
- `pylint>=3.0.0` - Static analysis

## Configuration

All tools configured in `pyproject.toml`:
- `[tool.black]` - Line length 88, target Python 3.12
- `[tool.isort]` - Black profile, line length 88
- `[tool.ruff]` - 9 rule categories, Python 3.12 target
- `[tool.pylint]` - Python 3.12, max line length 88
