# Security Policy

## Supported Versions

We take security seriously. The following versions of LANrage are currently supported with security updates:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.2.x   | :white_check_mark: | Current stable release |
| < 1.2   | :x:                | Older versions (not supported) |

## Security Features

LANrage implements multiple layers of security:

### Network Security
- **WireGuard Encryption** - Military-grade encryption (ChaCha20-Poly1305)
- **Perfect Forward Secrecy** - Unique keys for each session
- **Authenticated Encryption** - Prevents tampering and replay attacks
- **Key Rotation** - Automatic key refresh for long-running sessions

### Application Security
- **Input Validation** - All user inputs validated with Pydantic
- **SQL Injection Protection** - Parameterized queries with aiosqlite
- **Path Traversal Prevention** - Strict file path validation
- **Rate Limiting** - Protection against DoS attacks (planned for v1.1)
- **CORS Configuration** - Restricted to localhost by default

### Privacy
- **No Telemetry** - Zero data collection by default
- **Local-First** - All data stored locally (SQLite)
- **No Account Required** - Peer-to-peer architecture
- **Optional Discord Integration** - User controls all external connections

## Reporting a Vulnerability

We appreciate responsible disclosure of security vulnerabilities.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:

1. **Email**: security@lanrage.dev (preferred)
2. **GitHub Security Advisory**: Use the "Security" tab → "Report a vulnerability"
3. **Direct Message**: Contact @coff33ninja on GitHub

### What to Include

Please include the following information in your report:

- **Description** - Clear description of the vulnerability
- **Impact** - Potential security impact and severity
- **Steps to Reproduce** - Detailed reproduction steps
- **Proof of Concept** - Code or screenshots demonstrating the issue
- **Suggested Fix** - If you have ideas for remediation
- **Your Contact Info** - So we can follow up with questions

### Response Timeline

We aim to respond to security reports within:

- **24 hours** - Initial acknowledgment
- **7 days** - Preliminary assessment and severity rating
- **30 days** - Fix development and testing
- **90 days** - Public disclosure (coordinated with reporter)

### Severity Ratings

We use the following severity classifications:

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, authentication bypass | 24-48 hours |
| **High** | Privilege escalation, data exposure | 3-7 days |
| **Medium** | DoS, information disclosure | 7-14 days |
| **Low** | Minor issues with limited impact | 14-30 days |

## Security Best Practices

### For Users

1. **Keep Updated** - Always use the latest version of LANrage
2. **Verify Downloads** - Check file hashes when downloading
3. **Use Strong Keys** - Let WireGuard generate keys (don't reuse)
4. **Firewall Rules** - Only open necessary ports
5. **Trusted Peers** - Only connect to people you trust
6. **Monitor Logs** - Check `~/.lanrage/network.log` for suspicious activity
7. **Secure Your System** - Keep your OS and dependencies updated

### For Relay Operators

1. **Dedicated Server** - Use a dedicated machine for relay servers
2. **Firewall Configuration** - Restrict access to relay ports only
3. **Regular Updates** - Keep LANrage and system packages updated
4. **Monitor Resources** - Watch for unusual traffic patterns
5. **Rate Limiting** - Enable rate limiting (when available in v1.1)
6. **Logging** - Enable detailed logging for security audits
7. **Backup Keys** - Securely backup WireGuard keys

### For Developers

1. **Code Review** - All PRs require security review
2. **Dependency Scanning** - Regular audits of dependencies
3. **Static Analysis** - Use ruff and black for code quality
4. **Input Validation** - Validate all external inputs
5. **Secure Defaults** - Security-first configuration
6. **Error Handling** - Never expose sensitive info in errors
7. **Testing** - Include security tests in test suite

## Known Security Considerations

### Current Limitations

1. **Local/Hybrid Control Plane Limits** - some remote orchestration features are still evolving
   - **Mitigation**: Continue rollout of Phase 6 web-agent orchestration and auth hardening
   
2. **No Rate Limiting** - API endpoints lack rate limiting
   - **Mitigation**: Planned for v1.1, currently localhost-only reduces risk
   
3. **No User Authentication** - Party IDs are the only access control
   - **Mitigation**: Use strong, random party IDs (auto-generated)
   
4. **Relay Trust** - Relays can see encrypted traffic metadata
   - **Mitigation**: Use trusted relays or run your own

### Not Security Issues

The following are **not** considered security vulnerabilities:

- **Party ID Guessing** - Party IDs are meant to be shared
- **Relay Visibility** - Relays seeing encrypted packets is expected
- **Local API Access** - API is localhost-only by design
- **WireGuard Logs** - Connection logs are normal operation
- **Discord Integration** - Optional feature, user-controlled

## Security Updates

Security updates will be released as:

- **Patch Releases** - Critical/High severity (e.g., 1.2.6)
- **Minor Releases** - Medium severity (e.g., 1.3.0)
- **Announcements** - Posted on GitHub Releases and README

Subscribe to GitHub releases to receive security notifications.

## Compliance

LANrage is designed for personal and small-group gaming use. For enterprise or compliance-sensitive environments:

- Review the [Architecture Documentation](docs/ARCHITECTURE.md)
- Audit the [Source Code](https://github.com/coff33ninja/LANRage)
- Run your own relay servers
- Disable optional features (Discord, metrics)
- Implement additional security layers as needed

## Security Acknowledgments

We thank the following individuals for responsibly disclosing security issues:

- *No reports yet - be the first!*

## Contact

- **Security Email**: security@lanrage.dev
- **General Support**: support@lanrage.dev
- **GitHub Issues**: https://github.com/coff33ninja/LANRage/issues (non-security only)

## License

This security policy is part of the LANrage project and is licensed under the MIT License.

---

**Last Updated**: February 21, 2026  
**Version**: 1.2.5
