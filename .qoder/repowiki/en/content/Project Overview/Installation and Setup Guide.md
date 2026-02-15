# Installation and Setup Guide

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [QUICKSTART.md](file://docs/QUICKSTART.md)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md)
- [USER_GUIDE.md](file://docs/USER_GUIDE.md)
- [install_and_run.bat](file://install_and_run.bat)
- [install_and_run_advanced.bat](file://install_and_run_advanced.bat)
- [quick_install.bat](file://quick_install.bat)
- [setup.py](file://setup.py)
- [lanrage.py](file://lanrage.py)
- [requirements.txt](file://requirements.txt)
- [pyproject.toml](file://pyproject.toml)
- [.env.example](file://.env.example)
- [.env](file://.env)
- [settings.html](file://static/settings.html)
- [core/config.py](file://core/config.py)
- [core/settings.py](file://core/settings.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Platform-Specific Installation](#platform-specific-installation)
4. [Initial Configuration and First-Time Setup](#initial-configuration-and-first-time-setup)
5. [Web-Based Configuration Interface](#web-based-configuration-interface)
6. [Verification and Connectivity Checks](#verification-and-connectivity-checks)
7. [Backup and Recovery Procedures](#backup-and-recovery-procedures)
8. [Security Considerations and Network Best Practices](#security-considerations-and-network-best-practices)
9. [Troubleshooting Common Installation Issues](#troubleshooting-common-installation-issues)
10. [Conclusion](#conclusion)

## Introduction
This guide helps you install and set up LANrage quickly across Windows, Linux, and macOS. It covers command-line installation, automated batch scripts, manual setup, initial configuration, environment preparation, first-time onboarding, web UI configuration, verification steps, backup/recovery, and security/network best practices.

## Prerequisites
- Python 3.12+ (required)
- uv package manager (recommended)
- Administrative/root privileges for network interface creation
- WireGuard installed and functional
- Internet access for initial setup and optional updates

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)
- [README.md](file://README.md#L8-L14)

## Platform-Specific Installation

### Windows Installation
- Option 1: Automated scripts
  - Run the advanced installer for robust error handling and verification:
    - [install_and_run_advanced.bat](file://install_and_run_advanced.bat#L1-L235)
  - Run the standard installer for a streamlined experience:
    - [install_and_run.bat](file://install_and_run.bat#L1-L116)
  - Run the quick installer for minimal prompts:
    - [quick_install.bat](file://quick_install.bat#L1-L68)
- Option 2: Manual setup
  - Install uv (PowerShell):
    - [QUICKSTART.md](file://docs/QUICKSTART.md#L27-L37)
  - Install WireGuard (Windows):
    - [QUICKSTART.md](file://docs/QUICKSTART.md#L39-L43)
  - Clone and run setup:
    - [QUICKSTART.md](file://docs/QUICKSTART.md#L44-L50)
  - Activate virtual environment and run:
    - [QUICKSTART.md](file://docs/QUICKSTART.md#L58-L79)

Notes:
- The advanced installer verifies each step and provides fallbacks for failed components.
- The quick installer automates the same steps with fewer prompts.

**Section sources**
- [install_and_run_advanced.bat](file://install_and_run_advanced.bat#L1-L235)
- [install_and_run.bat](file://install_and_run.bat#L1-L116)
- [quick_install.bat](file://quick_install.bat#L1-L68)
- [QUICKSTART.md](file://docs/QUICKSTART.md#L27-L79)

### Linux/macOS Installation
- Install uv:
  - [QUICKSTART.md](file://docs/QUICKSTART.md#L34-L37)
- Install WireGuard:
  - [QUICKSTART.md](file://docs/QUICKSTART.md#L39-L43)
- Clone, run setup, activate venv, and start:
  - [QUICKSTART.md](file://docs/QUICKSTART.md#L44-L79)

Notes:
- On Linux, ensure administrative privileges for network interface creation.
- On macOS, install WireGuard tools similarly.

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L27-L79)

## Initial Configuration and First-Time Setup

### Using setup.py
- The setup script performs:
  - Validates Python version
  - Creates/activates virtual environment
  - Installs dependencies via uv
  - Initializes the settings database
  - Provides next steps for activation and running

- Key steps:
  - [setup.py](file://setup.py#L46-L96)

**Section sources**
- [setup.py](file://setup.py#L46-L96)

### Environment Setup
- Virtual environment creation and activation:
  - [QUICKSTART.md](file://docs/QUICKSTART.md#L58-L79)
- Dependencies:
  - [requirements.txt](file://requirements.txt#L1-L56)
  - [pyproject.toml](file://pyproject.toml#L26-L50)

Notes:
- The project uses uv for fast dependency installation.
- The legacy .env file is deprecated; configuration is now stored in a SQLite database.

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L56)
- [pyproject.toml](file://pyproject.toml#L26-L50)
- [.env.example](file://.env.example#L1-L36)
- [.env](file://.env#L1-L12)

### First Run and Database Initialization
- On first run, LANrage initializes the settings database and loads configuration from it:
  - [lanrage.py](file://lanrage.py#L53-L93)
  - [core/config.py](file://core/config.py#L49-L114)
  - [core/settings.py](file://core/settings.py#L476-L525)

**Section sources**
- [lanrage.py](file://lanrage.py#L53-L93)
- [core/config.py](file://core/config.py#L49-L114)
- [core/settings.py](file://core/settings.py#L476-L525)

## Web-Based Configuration Interface

### Accessing the Web UI
- Default URL: http://localhost:8666
- Settings page: http://localhost:8666/settings.html

**Section sources**
- [README.md](file://README.md#L83-L87)
- [QUICKSTART.md](file://docs/QUICKSTART.md#L96-L134)
- [settings.html](file://static/settings.html#L1-L684)

### Basic Setup Walkthrough
- Instance Mode: Choose Client or Relay
- Client Settings: Peer name, interface name, virtual subnet, keepalive, toggles for auto-optimization, broadcast, Discord, metrics
- Relay Settings: Public IP, port, max clients (when in relay mode)
- API Settings: Host and port
- Control Plane: Control server URL
- Discord Integration: App ID, webhook, invite
- Saved Configurations: Save and activate named configurations

**Section sources**
- [settings.html](file://static/settings.html#L304-L464)

## Verification and Connectivity Checks

### Post-Start Verification
- Confirm LANrage started successfully and shows expected components:
  - [QUICKSTART.md](file://docs/QUICKSTART.md#L78-L95)

### Connectivity Checks
- Use the web UI to verify:
  - NAT type detection
  - Connection type (Direct vs Relayed)
  - Latency and metrics
- Use the diagnostics from the troubleshooting guide:
  - [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L228-L246)

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L78-L95)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L228-L246)

## Backup and Recovery Procedures

### Database Backup and Integrity
- The settings database is stored at ~/.lanrage/settings.db
- The SettingsDatabase class provides:
  - Integrity checks
  - Size reporting
  - Backup via sqlite3 backup API

- Key methods:
  - [core/settings.py](file://core/settings.py#L371-L432)

### Recovery Steps
- If configuration becomes corrupted:
  - Use backup file if available
  - Reset to defaults via the web UI or API
  - Reconfigure settings through the web interface

**Section sources**
- [core/settings.py](file://core/settings.py#L371-L432)

## Security Considerations and Network Best Practices

### Security During Initial Setup
- Run with appropriate privileges:
  - Windows: Run as Administrator
  - Linux/macOS: Use sudo or grant required capabilities
- Keep WireGuard updated
- Use firewall rules to allow only necessary traffic (e.g., UDP 51820 for WireGuard)

### Network Configuration Best Practices
- Prefer wired connections for lower latency
- Close bandwidth-heavy applications during gaming sessions
- Ensure NAT traversal conditions allow direct P2P when possible
- Use the web UI to monitor connection type and adjust settings accordingly

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L164-L197)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L284-L310)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L462-L502)

## Troubleshooting Common Installation Issues

### WireGuard Not Found
- Install WireGuard:
  - Windows: Download installer
  - Linux: apt install wireguard
  - macOS: brew install wireguard-tools

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L39-L43)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L251-L281)

### Permission Denied
- Run with elevated privileges:
  - Windows: Run as Administrator
  - Linux/macOS: sudo

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L284-L310)

### Python Version Error
- Ensure Python 3.12+ is installed and on PATH

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L312-L340)

### Dependencies Installation Failed
- Update uv, install with verbose output, verify internet connectivity, install build tools if needed

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L342-L370)

### Cannot Create/Join Party
- Check internet connectivity, firewall rules, and NAT type
- Use local mode temporarily if needed

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L374-L424)

### Peer Connection Failed
- Check firewall allows UDP 51820, try different networks, reduce congestion

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L426-L460)

### High Latency
- Prefer direct connections, wired connections, close bandwidth-heavy apps, optimize game settings

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L462-L502)

### Game-Specific Issues
- Use broadcast emulation for LAN games, verify virtual IPs, follow game-specific guidance

**Section sources**
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L541-L621)

## Conclusion
You now have the essential steps to install LANrage, configure it via the web UI, verify connectivity, and troubleshoot common issues. For deeper guidance, consult the User Guide and Troubleshooting documents linked below.

**Section sources**
- [USER_GUIDE.md](file://docs/USER_GUIDE.md#L1-L435)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L1-L904)