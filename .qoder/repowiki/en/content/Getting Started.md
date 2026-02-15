# Getting Started

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [QUICKSTART.md](file://docs/QUICKSTART.md)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md)
- [quick_install.bat](file://quick_install.bat)
- [install_and_run.bat](file://install_and_run.bat)
- [requirements.txt](file://requirements.txt)
- [pyproject.toml](file://pyproject.toml)
- [lanrage.py](file://lanrage.py)
- [setup.py](file://setup.py)
- [core/config.py](file://core/config.py)
- [core/settings.py](file://core/settings.py)
- [.env.example](file://.env.example)
- [api/server.py](file://api/server.py)
- [static/index.html](file://static/index.html)
- [core/party.py](file://core/party.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites and System Requirements](#prerequisites-and-system-requirements)
3. [Installation Methods](#installation-methods)
4. [Quick Start in 90 Seconds](#quick-start-in-90-seconds)
5. [First-Time Setup and Verification](#first-time-setup-and-verification)
6. [Web UI Access and Basic Navigation](#web-ui-access-and-basic-navigation)
7. [Party Creation Workflow](#party-creation-workflow)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Verification Checklist](#verification-checklist)
10. [Conclusion](#conclusion)

## Introduction
LANrage lets you play LAN-style games over the internet with minimal setup. It creates a secure, low-latency mesh VPN using WireGuard, handles NAT traversal automatically, and provides a simple web interface for managing parties and settings. This guide walks you through installation, initial configuration, and your first gaming session.

## Prerequisites and System Requirements
- Operating systems:
  - Windows 10/11
  - Linux distributions (Ubuntu/Debian preferred)
  - macOS (limited official support; see Troubleshooting)
- Software requirements:
  - Python 3.12 or newer
  - uv package manager
  - WireGuard installed and functional
  - Administrative/root privileges for network interface creation
- Ports:
  - UDP 51820 for WireGuard data plane
  - Web UI listens on localhost:8666 by default

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)
- [README.md](file://README.md#L8-L14)

## Installation Methods
LANrage supports multiple installation approaches. Choose the one that fits your environment.

### Option A: One-Click Windows Installer
- Run the quick installer with administrative privileges.
- It installs Chocolatey, Python 3.12, uv, sets up a virtual environment, installs dependencies, and starts LANrage.

```text
Double-click quick_install.bat (run as Administrator)
```

**Section sources**
- [quick_install.bat](file://quick_install.bat#L1-L68)

### Option B: Complete Windows Installer
- Full automation including dependency updates and initial setup.

```text
Double-click install_and_run.bat (run as Administrator)
```

**Section sources**
- [install_and_run.bat](file://install_and_run.bat#L1-L116)

### Option C: Manual Installation (Windows/Linux/macOS)
- Install uv and Python 3.12+.
- Install WireGuard for your OS.
- Clone the repository and run the setup script.

```text
git clone https://github.com/yourusername/lanrage.git
cd lanrage
python setup.py
```

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L25-L51)
- [setup.py](file://setup.py#L46-L96)

### Dependency Management
- Core dependencies are defined in the project metadata and requirements file.
- The setup script uses uv to create a virtual environment and install packages.

**Section sources**
- [pyproject.toml](file://pyproject.toml#L26-L50)
- [requirements.txt](file://requirements.txt#L15-L56)
- [setup.py](file://setup.py#L70-L74)

## Quick Start in 90 Seconds
Follow this streamlined process to get LANrage running immediately.

1. Install uv and Python 3.12+.
2. Install WireGuard.
3. Clone the repository and run the setup script.
4. Activate the virtual environment.
5. Start LANrage.
6. Open the web UI in your browser.
7. Create a party and invite friends.

```text
git clone https://github.com/yourusername/lanrage.git
cd lanrage
python setup.py
# Activate environment (see OS-specific steps below)
python lanrage.py
# Open http://localhost:8666 in your browser
```

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L25-L95)
- [README.md](file://README.md#L57-L88)

## First-Time Setup and Verification
After installation, verify that LANrage initializes correctly and creates a local VPN interface.

### Windows
- Run as Administrator.
- Expected console output indicates successful initialization of the network, NAT traversal, control plane, and API server.

```text
python lanrage.py
```

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L70-L95)
- [lanrage.py](file://lanrage.py#L94-L150)

### Linux/macOS
- Use sudo or grant appropriate capabilities if required.
- Ensure WireGuard kernel modules are available.

```text
sudo python lanrage.py
```

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L70-L95)
- [lanrage.py](file://lanrage.py#L94-L106)

### Configuration Storage
- LANrage stores all settings in a SQLite database located at ~/.lanrage/settings.db.
- The legacy .env file is deprecated; configure via the Web UI.

**Section sources**
- [core/settings.py](file://core/settings.py#L466-L473)
- [.env.example](file://.env.example#L1-L36)

## Web UI Access and Basic Navigation
LANrage exposes a web-based dashboard for managing parties, servers, metrics, Discord integration, and settings.

- Default URL: http://localhost:8666
- Tabs:
  - Party: Create or join parties, manage connections
  - Servers: Discover and join hosted game servers
  - Metrics: View latency, quality, and system stats
  - Discord: Configure webhook and invite links
  - Settings: Adjust mode, network, API, and integrations

```text
Open http://localhost:8666 in your browser
```

**Section sources**
- [api/server.py](file://api/server.py#L113-L121)
- [static/index.html](file://static/index.html#L715-L722)

## Party Creation Workflow
Create a party, invite friends, and start gaming.

### Host Creates Party
1. Open the Party tab in the web UI.
2. Click “Create Party” and enter a party name.
3. Copy the generated Party ID and share it with friends.

```text
Party tab → Create Party → Enter name → Copy Party ID
```

**Section sources**
- [static/index.html](file://static/index.html#L727-L746)
- [api/server.py](file://api/server.py#L155-L162)

### Friends Join Party
1. Open the Party tab.
2. Click “Join Party.”
3. Enter the Party ID and your display name.
4. Click “Join.”

```text
Party tab → Join Party → Enter Party ID and name → Join
```

**Section sources**
- [static/index.html](file://static/index.html#L748-L761)
- [api/server.py](file://api/server.py#L165-L175)

### Connection Types and NAT
- LANrage detects NAT type and attempts direct P2P connections when possible.
- Symmetric NATs may require relay fallback.

```text
Check NAT type and connection type in the UI
```

**Section sources**
- [core/party.py](file://core/party.py#L121-L143)

## Troubleshooting Common Issues
Encounter a problem? Use these targeted fixes.

### Permission Denied
- Run as Administrator (Windows) or with sudo/root (Linux/macOS).
- On Linux, you may need to grant capabilities or add the user to the netdev group.

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L166-L170)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L284-L310)

### WireGuard Not Found
- Install WireGuard:
  - Windows: Download installer from the official site
  - Linux: Use apt to install wireguard/wireguard-tools
  - macOS: Use Homebrew to install wireguard-tools

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L171-L176)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L251-L281)

### Port 8666 Already in Use
- Change the API port in Settings or via the .env file (deprecated; use Web UI).

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L177-L182)
- [.env.example](file://.env.example#L16-L35)

### Friends Cannot Join
- Verify the Party ID is correct and matches exactly.
- Ensure both hosts and clients are running the same LANrage version.
- Check firewall rules allow UDP 51820.
- Confirm NAT type; symmetric NATs often require relay.

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L184-L189)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L426-L460)

### High Latency
- Prefer direct connections; avoid relay when possible.
- Use a wired connection, close bandwidth-heavy apps, and reduce background traffic.
- If using relay, choose a geographically closer relay server.

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L191-L197)
- [TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L462-L502)

### Game Does Not See Other Players
- Confirm all players are in the same party.
- Ensure the WireGuard interface is active and the virtual subnet is correct.
- Some games require specific ports or broadcast/multicast emulation.

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L198-L204)
- [core/config.py](file://core/config.py#L24-L25)

## Verification Checklist
Ensure everything is working properly before inviting friends.

- [ ] LANrage started without errors and shows “API server running” on localhost:8666
- [ ] Network interface initialized (Windows: netsh interface; Linux/macOS: ip addr)
- [ ] NAT type detected and connection type shown in UI
- [ ] Party created successfully and peers can connect
- [ ] Web UI tabs load without errors
- [ ] Settings saved to ~/.lanrage/settings.db (not .env)

**Section sources**
- [QUICKSTART.md](file://docs/QUICKSTART.md#L78-L95)
- [lanrage.py](file://lanrage.py#L94-L150)
- [core/settings.py](file://core/settings.py#L466-L473)

## Conclusion
You are now ready to play LAN-style games over the internet with LANrage. Use the Web UI to manage parties, servers, and settings. If you encounter issues, consult the Troubleshooting guide or the project’s documentation. For persistent problems, gather diagnostic information and open an issue with your logs and environment details.