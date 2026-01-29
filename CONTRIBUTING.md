# Contributing to LANrage

## Current Status

LANrage is currently a **solo project** in early prototype phase. I'm not actively accepting contributions yet, but that will change.

## Future Contributions

Once the core is stable (Phase 3+), I'll open up contributions for:
- Bug fixes
- Game profiles
- Platform support
- Documentation
- Testing

## How to Help Now

### 1. Test It

The best way to help is to test LANrage and report issues:
- Try it with different games
- Test on different networks
- Report bugs on GitHub Issues
- Share your experience

### 2. Spread the Word

- Tell your gaming friends
- Share on Reddit/Discord
- Stream it on Twitch
- Write about it

### 3. Provide Feedback

- What games do you want to work?
- What features are missing?
- What's confusing?
- What's broken?

### 4. Donate (Future)

Once there's a Patreon/Ko-fi, support the project financially.

## Bug Reports

### Good Bug Report

```markdown
**Title**: Minecraft LAN discovery not working

**Environment**:
- LANrage version: 0.1.0
- OS: Windows 11
- Game: Minecraft Java 1.20.4
- Network: Behind NAT

**Expected**: See friend's server in LAN list
**Actual**: No servers shown

**Steps to Reproduce**:
1. Create party
2. Friend joins party
3. Friend hosts Minecraft server
4. Open LAN game list
5. No servers appear

**Logs**: (attach ~/.lanrage/logs/lanrage.log)

**Additional Info**:
- Direct IP connection works
- Both can ping each other (10.66.0.x)
- Firewall disabled
```

### Bad Bug Report

```markdown
**Title**: It doesn't work

**Description**: I tried to use it and it didn't work. Fix it.
```

## Feature Requests

### Good Feature Request

```markdown
**Title**: Add support for Age of Empires II

**Problem**: AoE2 uses IPX protocol for LAN games

**Proposed Solution**: 
- Emulate IPX over IP
- Translate IPX broadcasts
- Add AoE2 game profile

**Alternatives Considered**:
- Use existing IPX wrapper
- Manual port forwarding (defeats the purpose)

**Priority**: High (popular game)
```

### Bad Feature Request

```markdown
**Title**: Add everything

**Description**: Make it work with all games ever made.
```

## Code Style

When contributions open up:

### Python

- Python 3.12+
- Type hints everywhere
- Black formatting
- Ruff linting
- Docstrings for public APIs

### Example

```python
async def measure_latency(peer_ip: str, count: int = 10) -> float:
    """
    Measure latency to a peer.
    
    Args:
        peer_ip: Virtual IP of the peer
        count: Number of pings to average
        
    Returns:
        Average latency in milliseconds
        
    Raises:
        NetworkError: If peer is unreachable
    """
    # Implementation
    pass
```

## Commit Messages

### Good

```
fix: Minecraft broadcast emulation not working

- Add UDP broadcast capture
- Re-emit to all party members
- Handle address translation

Fixes #42
```

### Bad

```
fixed stuff
```

## Pull Request Process

(When contributions open)

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit PR
7. Wait for review

## Testing

All PRs must include:
- Unit tests
- Integration tests (if applicable)
- Manual testing notes

## Documentation

All features must be documented:
- Code comments
- API documentation
- User-facing docs
- Examples

## License

By contributing, you agree to license your contributions under the MIT License.

## Code of Conduct

### Be Cool

- Be respectful
- Be constructive
- Be patient
- Be helpful

### Don't Be a Jerk

- No harassment
- No spam
- No trolling
- No gatekeeping

### Consequences

- First offense: Warning
- Second offense: Temporary ban
- Third offense: Permanent ban

## Communication

### GitHub Issues

- Bug reports
- Feature requests
- Technical discussions

### Discord (Future)

- General chat
- Support
- Community

### Reddit (Future)

- Announcements
- Discussions
- Memes

## Roadmap Influence

Want to influence the roadmap?
- Comment on GitHub Issues
- Vote with 👍 reactions
- Provide use cases
- Share your experience

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given eternal glory

## Questions?

- Open a GitHub Issue
- Tag it with "question"
- I'll respond ASAP

## Thank You

Thanks for your interest in LANrage. Even if you're just reading this, you're helping make gaming better.

Now go play some games. 🎮
