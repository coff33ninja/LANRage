# Contributing to LANrage

## Current Status

LANrage v1.2.5 is **production ready** and open for contributions.

**Current baseline**: 463/463 tests passing in latest full-suite run.

We welcome contributions for:
- 🐛 Bug fixes
- 🎮 Game profiles
- 🖥️ Platform support
- 📚 Documentation
- 🧪 Testing
- ✨ Feature enhancements

---

## Quick Start for Contributors

### 1. Setup Development Environment

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/LANRage.git
cd lanrage

# Run setup
python setup.py

# Activate virtual environment
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac

# Verify setup
python lanrage.py
```

### 2. Run Tests

```bash
# Run all tests
.venv\Scripts\python.exe -m pytest tests/  # Windows
.venv/bin/python -m pytest tests/          # Linux/Mac

# Run specific test
pytest tests/test_nat.py -v

# Check coverage
pytest --cov=core --cov=api tests/
```

### 3. Code Quality

```bash
# Run all quality checks (in order)
.venv\Scripts\python.exe -m isort .              # Sort imports
.venv\Scripts\python.exe -m black .              # Format code
.venv\Scripts\python.exe -m ruff check --fix .   # Lint and fix
.venv\Scripts\python.exe -m pytest tests/        # Run tests
```

All checks must pass before submitting PR.

---

## How to Contribute

### 🐛 Bug Fixes

1. Check if issue already exists
2. Create issue if not (use bug report template)
3. Fork and create branch: `fix/issue-description`
4. Fix the bug with tests
5. Submit PR referencing issue

### 🎮 Game Profiles

Adding a new game is easy!

**Create**: `game_profiles/custom/your_game.json`

```json
{
  "your_game": {
    "name": "Your Game Name",
    "executable": "game.exe",
    "ports": [12345],
    "protocol": "udp",
    "broadcast": true,
    "multicast": false,
    "keepalive": 25,
    "mtu": 1420,
    "description": "Game description",
    "low_latency": true,
    "high_bandwidth": false,
    "packet_priority": "high"
  }
}
```

**Test**: Verify game detection and optimization work.

**Submit**: PR with game profile + testing notes.

### 📚 Documentation

- Fix typos and errors
- Add examples and tutorials
- Improve clarity
- Translate to other languages (future)

### 🧪 Testing

- Add test cases for edge cases
- Improve test coverage
- Add integration tests
- Performance benchmarks

### ✨ Features

For new features:
1. Open issue first to discuss
2. Get approval before coding
3. Follow architecture patterns
4. Include tests and docs
5. Submit PR

---

## Bug Reports

### Good Bug Report Template

```markdown
**Title**: Clear, specific description

**Environment**:
- LANrage version: 1.2.5
- OS: Windows 11 / Ubuntu 22.04
- Python: 3.12.1
- Game: Minecraft Java 1.20.4
- Network: Behind NAT / Direct connection

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Logs**: 
```
Paste relevant logs from ~/.lanrage/network.log
```

**Additional Context**:
- Screenshots if applicable
- Network topology diagram
- Related issues
```

### What Makes a Good Bug Report

✅ **Good**:
- Specific and reproducible
- Includes environment details
- Has logs and error messages
- Clear steps to reproduce
- Expected vs actual behavior

❌ **Bad**:
- "It doesn't work"
- No details or context
- Can't reproduce
- No logs or errors

---

## Feature Requests

### Good Feature Request Template

```markdown
**Title**: Concise feature description

**Problem**: What problem does this solve?

**Proposed Solution**: How should it work?

**Alternatives Considered**: Other approaches?

**Use Case**: Real-world scenario

**Priority**: High / Medium / Low

**Willing to Implement**: Yes / No / Need guidance
```

### Feature Request Guidelines

- Check if already requested
- Explain the "why" not just "what"
- Consider implementation complexity
- Think about edge cases
- Be open to alternatives

---

## Code Style & Standards

### Python Style

- **Python Version**: 3.12+
- **Formatting**: Black (line length 88)
- **Import Sorting**: isort
- **Linting**: Ruff
- **Type Hints**: Required for all public APIs
- **Docstrings**: Required for public functions/classes

### Example Code

```python
async def measure_latency(peer_ip: str, count: int = 10) -> float:
    """
    Measure latency to a peer using ICMP ping.
    
    Args:
        peer_ip: Virtual IP address of the peer (10.66.x.x)
        count: Number of pings to average (default: 10)
        
    Returns:
        Average latency in milliseconds
        
    Raises:
        NetworkError: If peer is unreachable
        ValueError: If count < 1
        
    Example:
        >>> latency = await measure_latency("10.66.0.2")
        >>> print(f"Latency: {latency:.2f}ms")
        Latency: 12.34ms
    """
    if count < 1:
        raise ValueError("count must be >= 1")
    
    # Implementation
    pass
```

### Code Quality Checklist

Before submitting PR:
- [ ] Code formatted with Black
- [ ] Imports sorted with isort
- [ ] No Ruff warnings
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Tests added/updated
- [ ] Tests passing (100%)
- [ ] Documentation updated

---

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Examples

✅ **Good**:
```
feat(games): add Age of Empires II profile

- Add game detection for AoE2
- Configure broadcast emulation for IPX
- Set optimal keepalive and MTU
- Add integration test

Closes #123
```

```
fix(nat): handle symmetric NAT detection edge case

STUN detection was failing when both peers had symmetric NAT.
Now properly falls back to relay in this scenario.

Fixes #456
```

❌ **Bad**:
```
fixed stuff
```

```
update
```

---

## Pull Request Process

### Before Submitting

1. **Fork** the repository
2. **Create branch**: `feat/your-feature` or `fix/issue-123`
3. **Make changes** following code style
4. **Add tests** for new functionality
5. **Update docs** if needed
6. **Run quality checks** (isort, black, ruff, pytest)
7. **Commit** with good messages
8. **Push** to your fork

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring
- [ ] Test improvement

## Related Issues
Fixes #123
Closes #456

## Testing
- [ ] All existing tests pass
- [ ] Added new tests
- [ ] Manually tested

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks** run (tests, linting)
2. **Code review** by maintainer
3. **Feedback** and requested changes
4. **Approval** when ready
5. **Merge** into main branch

### Review Timeline

- Initial response: 1-3 days
- Full review: 3-7 days
- Complex features: 1-2 weeks

---

## Testing Guidelines

### Test Requirements

All PRs must include:
- **Unit tests** for new functions
- **Integration tests** for features
- **Manual testing** notes

### Test Structure

```python
import pytest
from core.nat import NATTraversal

@pytest.mark.asyncio
async def test_nat_detection():
    """Test NAT type detection via STUN"""
    nat = NATTraversal(config)
    response = await nat.detect_nat()
    
    assert response.nat_type is not None
    assert response.public_ip is not None
    assert response.public_port > 0
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_nat.py

# Specific test
pytest tests/test_nat.py::test_nat_detection

# With coverage
pytest --cov=core tests/

# Verbose
pytest -v tests/
```

---

## Documentation Guidelines

### What to Document

- **Public APIs**: All functions/classes
- **Features**: User-facing functionality
- **Setup**: Installation and configuration
- **Examples**: Real-world usage
- **Troubleshooting**: Common issues

### Documentation Locations

- **Code**: Docstrings in Python files
- **API**: `docs/API.md`
- **User Guide**: `docs/USER_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`

### Documentation Style

- Clear and concise
- Include examples
- Use proper formatting
- Link to related docs
- Keep up to date

---

## Project Structure

```
lanrage/
├── api/              # FastAPI REST API
├── core/             # Core networking logic
├── servers/          # Control plane and relay servers
├── static/           # Web UI (HTML/CSS/JS)
├── tests/            # Test suites
├── docs/             # Documentation
├── game_profiles/    # Game detection profiles
├── .kiro/            # Kiro AI configuration
├── lanrage.py        # Main entry point
└── requirements.txt  # Dependencies
```

### Key Modules

- `core/network.py` - WireGuard management
- `core/nat.py` - NAT traversal
- `core/party.py` - Party management
- `core/games.py` - Game detection
- `core/control_client.py` - Control plane client
- `servers/control_server.py` - Control plane server

---

## Communication Channels

### GitHub Issues
- 🐛 Bug reports
- ✨ Feature requests
- 💬 Technical discussions
- ❓ Questions

### GitHub Discussions (Future)
- General chat
- Ideas and brainstorming
- Show and tell
- Q&A

### Discord (Future)
- Real-time chat
- Community support
- Development updates
- Gaming sessions

### Reddit (Future)
- Announcements
- Community discussions
- Memes and fun

---

## Recognition

Contributors will be:
- ✨ Listed in `CONTRIBUTORS.md`
- 📢 Mentioned in release notes
- 🏆 Given eternal glory
- 💖 Appreciated forever

---

## Code of Conduct

### Be Excellent to Each Other

✅ **Do**:
- Be respectful and kind
- Be constructive in feedback
- Be patient with newcomers
- Be helpful and supportive
- Celebrate others' contributions

❌ **Don't**:
- Harass or discriminate
- Spam or troll
- Be dismissive or rude
- Gatekeep or exclude
- Violate privacy

### Enforcement

1. **First offense**: Warning
2. **Second offense**: Temporary ban (1 week)
3. **Third offense**: Permanent ban

Serious violations (harassment, threats) result in immediate permanent ban.

---

## License

By contributing, you agree to license your contributions under the **MIT License**.

Your contributions will be:
- Open source forever
- Free to use and modify
- Attributed to you
- Part of something awesome

---

## Questions?

- 📖 Check the [User Guide](docs/USER_GUIDE.md)
- 🔍 Search existing issues
- 💬 Open a new issue with "question" label
- 📧 Email: support@lanrage.dev (future)

---

## Thank You! 🎉

Thank you for contributing to LANrage! Whether you're fixing a typo, adding a game profile, or building a major feature, every contribution makes gaming better for everyone.

Now go play some games! 🎮

---

**LANrage v1.2.5 - Production Ready**  
*If it runs on LAN, it runs on LANrage.*
