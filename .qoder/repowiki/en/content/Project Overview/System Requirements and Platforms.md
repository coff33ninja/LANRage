# System Requirements and Platforms

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [pyproject.toml](file://pyproject.toml)
- [requirements.txt](file://requirements.txt)
- [setup.py](file://setup.py)
- [install_and_run.bat](file://install_and_run.bat)
- [quick_install.bat](file://quick_install.bat)
- [install_and_run_advanced.bat](file://install_and_run_advanced.bat)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md)
- [docs/NETWORK.md](file://docs/NETWORK.md)
- [docs/QUICKSTART.md](file://docs/QUICKSTART.md)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md)
- [docs/PERFORMANCE_OPTIMIZATION.md](file://docs/PERFORMANCE_OPTIMIZATION.md)
- [lanrage.py](file://lanrage.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Supported Operating Systems](#supported-operating-systems)
3. [Hardware Requirements](#hardware-requirements)
4. [Python and Dependency Requirements](#python-and-dependency-requirements)
5. [Platform-Specific Considerations](#platform-specific-considerations)
6. [Installation Prerequisites](#installation-prerequisites)
7. [Compatibility Notes](#compatibility-notes)
8. [System Preparation Checklist](#system-preparation-checklist)
9. [Virtualization and Container Deployment](#virtualization-and-container-deployment)
10. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Introduction
This document provides comprehensive system requirements and platform compatibility guidance for LANrage. It covers supported operating systems, hardware specifications, Python and dependency requirements, platform-specific considerations for WireGuard and network interfaces, administrative privileges, compatibility with gaming platforms and network environments, system preparation steps, driver requirements, potential conflicts with existing VPN software, and virtualization/container deployment considerations.

## Supported Operating Systems
LANrage supports the following operating systems:

- **Windows 10/11**: Fully supported with native WireGuard integration and administrative privilege requirements for interface management.
- **Linux (Ubuntu/Debian)**: Fully supported with kernel module and command-line tool requirements.
- **macOS**: Currently untested and not officially supported by the project maintainers.

Platform-specific installation and privilege requirements are detailed below.

**Section sources**
- [docs/QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L16-L55)
- [docs/NETWORK.md](file://docs/NETWORK.md#L289-L324)

## Hardware Requirements
LANrage is designed for low-resource consumption suitable for most modern gaming setups. Based on performance profiling and optimization targets:

### Minimum Specifications
- **CPU**: Intel Core i5-12400F or AMD Ryzen 5 3600 equivalent
- **Memory**: 8 GB RAM (16 GB recommended)
- **Storage**: 2 GB available disk space
- **Network**: Gigabit Ethernet preferred; WiFi 802.11ax/AC acceptable
- **Graphics**: Integrated graphics sufficient for gaming; dedicated GPU optional

### Recommended Specifications
- **CPU**: Intel Core i7-12700K or AMD Ryzen 7 5800X or newer
- **Memory**: 16 GB RAM (32 GB recommended)
- **Storage**: SSD with 5 GB free space
- **Network**: Wired Ethernet connection for optimal latency
- **Graphics**: Mid-range GPU or better

### Performance Targets
- **Latency**: Direct P2P <5ms overhead; Relayed <15ms overhead
- **Throughput**: >90% of baseline network throughput
- **CPU Usage**: <5% idle; <15% active gaming
- **Memory Usage**: <100MB per client

**Section sources**
- [docs/PERFORMANCE_OPTIMIZATION.md](file://docs/PERFORMANCE_OPTIMIZATION.md#L10-L25)
- [docs/PERFORMANCE_OPTIMIZATION.md](file://docs/PERFORMANCE_OPTIMIZATION.md#L17-L21)
- [docs/NETWORK.md](file://docs/NETWORK.md#L325-L350)

## Python and Dependency Requirements
LANrage requires Python 3.12 or later and uses the uv package manager for dependency installation.

### Python Version Requirement
- **Required**: Python >= 3.12
- **Recommended**: Python 3.12.x for optimal compatibility

### Core Dependencies
The project uses the following key dependencies:
- **WireGuard**: wireguard-tools>=0.4.0 for interface management
- **Networking**: pyroute2>=0.7.12, scapy>=2.5.0
- **NAT Traversal**: aiortc>=1.9.0, aioice>=0.9.0
- **Web Framework**: fastapi>=0.115.0, uvicorn>=0.32.0, websockets>=13.1
- **HTTP Client**: httpx>=0.27.0
- **Utilities**: pydantic>=2.10.0, cryptography>=44.0.0, python-dotenv>=1.0.1, psutil>=6.1.0, aiohttp>=3.9.0, aiosqlite>=0.20.0, aiofiles>=24.10

### Optional Dependencies
- **Discord Integration**: pypresence>=4.3.0 (Rich Presence), discord.py>=2.3.0 (Bot)
- **Development Tools**: black>=23.3.0, isort>=5.12.0, ruff>=0.1.0, pylint>=3.0.0, pytest>=7.0.0

### Package Manager
- **Primary**: uv (recommended) for fast dependency resolution and installation
- **Fallback**: pip when uv is unavailable

**Section sources**
- [pyproject.toml](file://pyproject.toml#L10)
- [pyproject.toml](file://pyproject.toml#L26-L50)
- [requirements.txt](file://requirements.txt#L1-L56)
- [setup.py](file://setup.py#L53-L74)

## Platform-Specific Considerations
This section details platform-specific requirements for WireGuard, network interface management, and administrative privileges.

### Windows
- **WireGuard Installation**: Download from official WireGuard website; verify with `wireguard --version`
- **Administrative Privileges**: Required for interface creation and service management
- **Service Management**: Uses Windows service (`WireGuardTunnel$lanrage0`) for persistent configuration
- **Interface Limitations**: Cannot dynamically update configuration; service reinstall required for key changes

### Linux
- **WireGuard Installation**: `sudo apt install wireguard` (Ubuntu/Debian), `sudo dnf install wireguard-tools` (Fedora), `sudo pacman -S wireguard-tools` (Arch)
- **Root/Sudo Access**: Required for interface creation and configuration
- **Kernel Modules**: Ensure WireGuard kernel module is loaded (`lsmod | grep wireguard`)
- **Command Availability**: `ip` and `wg` commands must be available

### macOS
- **Status**: Unofficially supported; not tested by maintainers
- **Assumed Requirements**: wireguard-tools installation via Homebrew, similar privilege requirements as Linux

### Administrative Privileges
- **Windows**: Run as Administrator
- **Linux**: Use `sudo` or configure passwordless sudo for wg and ip commands
- **macOS**: Similar to Linux; use sudo or appropriate permissions

**Section sources**
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L16-L55)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L125-L217)
- [docs/NETWORK.md](file://docs/NETWORK.md#L289-L324)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L284-L310)

## Installation Prerequisites
Follow these steps to prepare your system for LANrage installation:

### System Preparation
1. **Verify Python Version**: Ensure Python 3.12+ is installed and accessible
2. **Install uv Package Manager**: Download from https://docs.astral.sh/uv/
3. **WireGuard Installation**: Install according to platform-specific instructions
4. **Administrative Privileges**: Ensure you have admin/root access for network operations

### Windows-Specific Steps
- Run installation scripts with Administrator privileges
- Verify WireGuard installation and PATH configuration
- Ensure Windows Firewall allows LANrage and WireGuard traffic

### Linux-Specific Steps
- Add user to sudoers or configure passwordless sudo for wg and ip commands
- Verify kernel module availability and load if necessary
- Ensure firewall allows UDP 51820 traffic

### macOS-Specific Steps
- Install wireguard-tools via Homebrew
- Ensure appropriate permissions for network interface management

**Section sources**
- [docs/QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)
- [install_and_run.bat](file://install_and_run.bat#L9-L16)
- [install_and_run_advanced.bat](file://install_and_run_advanced.bat#L23-L33)
- [docs/WIREGUARD_SETUP.md](file://docs/WIREGUARD_SETUP.md#L16-L55)

## Compatibility Notes
LANrage provides compatibility across various gaming platforms and network environments through its virtual LAN approach.

### Gaming Platform Compatibility
- **Direct LAN Games**: Native compatibility with games supporting LAN play
- **Online Games**: Compatible with games using TCP/UDP protocols
- **Steam/Origin/Epic**: Compatible with Steam, Epic, and other digital distribution platforms
- **Custom Game Profiles**: JSON-based profiles support custom game configurations

### Network Environment Compatibility
- **NAT Types**: Supports Open, Moderate, Strict, and Symmetric NAT configurations
- **Relay Fallback**: Automatic fallback to relay servers for difficult NAT scenarios
- **Broadcast Emulation**: Provides LAN-like broadcast capabilities for legacy games
- **Multi-Peer Mesh**: Supports up to 255 peers in a single party

### VPN Software Conflicts
- **Existing VPNs**: May conflict with LANrage's WireGuard interface management
- **Conflicting Interfaces**: Multiple VPN clients can cause interface name conflicts
- **Port Conflicts**: UDP 51820 may be occupied by other VPN software
- **Recommendation**: Uninstall or temporarily disable existing VPN software before LANrage installation

**Section sources**
- [docs/NETWORK.md](file://docs/NETWORK.md#L267-L288)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L426-L460)

## System Preparation Checklist
Complete these steps before installing LANrage:

### Pre-Installation Verification
- [ ] Confirm Python 3.12+ installation
- [ ] Verify uv package manager availability
- [ ] Check administrative/root privileges
- [ ] Ensure WireGuard installation matches platform requirements
- [ ] Verify system meets minimum hardware specifications

### Network Configuration
- [ ] Configure firewall to allow UDP 51820
- [ ] Ensure router port forwarding is disabled (WireGuard handles NAT traversal)
- [ ] Verify network stability and bandwidth availability
- [ ] Test basic network connectivity

### Driver Requirements
- [ ] Install latest network drivers
- [ ] Ensure network adapter supports gigabit speeds
- [ ] Verify wireless drivers if using WiFi (prefer wired connections)

### Existing Software Check
- [ ] Uninstall conflicting VPN software
- [ ] Disable Windows Defender Firewall exceptions if causing conflicts
- [ ] Check for antivirus software that might block network operations

**Section sources**
- [docs/QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L251-L281)

## Virtualization and Container Deployment
LANrage can be deployed in virtualized environments, though certain considerations apply.

### Virtual Machine Considerations
- **Network Passthrough**: Prefer bridged networking for optimal performance
- **Nested Virtualization**: Enable VT-x/AMD-V in VM settings
- **Resource Allocation**: Allocate at least 2 vCPUs and 2GB RAM
- **Disk Performance**: Use SSD-backed storage for VM disks

### Container Deployment
- **Docker**: Possible with proper host networking configuration
- **Host Network Mode**: Required for WireGuard interface access
- **Privileged Mode**: May be necessary for network interface management
- **Volume Mounts**: Persistent storage for configuration and keys

### Cloud Deployment
- **Oracle Cloud**: Project specifically mentions Oracle VPS as suitable for relay servers
- **Resource Requirements**: Minimum 1GB RAM, 20GB SSD, 1 vCPU recommended
- **Network Configuration**: Ensure UDP 51820 is accessible from the internet

**Section sources**
- [README.md](file://README.md#L55)
- [docs/QUICKSTART.md](file://docs/QUICKSTART.md#L17-L24)

## Troubleshooting Common Issues
This section addresses frequently encountered problems during installation and operation.

### Installation Issues
- **"WireGuard not found"**: Install WireGuard according to platform-specific instructions
- **"Permission denied"**: Run with administrative privileges or sudo access
- **Python version errors**: Install Python 3.12+ and ensure PATH configuration
- **Dependency installation failures**: Update uv, check internet connectivity, install build tools

### Network Interface Problems
- **Interface creation failures**: Check for conflicting interfaces, verify permissions, review logs
- **Peer connection failures**: Verify firewall settings, check NAT type, ensure UDP 51820 is open
- **High latency**: Use wired connection, close bandwidth-heavy applications, optimize network settings

### Performance Issues
- **High CPU usage**: Disable unused features, reduce metrics collection frequency, restart LANrage
- **Memory usage concerns**: Clear metrics history, reduce server browser refresh rates
- **Slow Web UI**: Use modern browsers, disable extensions, adjust polling intervals

### Game-Specific Issues
- **Games not detecting LANrage**: Verify broadcast emulation is enabled, check virtual IP assignments
- **Specific game compatibility**: Use custom game profiles, adjust MTU and port settings
- **Connection timeouts**: Check NAT traversal, verify game-specific port requirements

**Section sources**
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L249-L371)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L372-L503)
- [docs/TROUBLESHOOTING.md](file://docs/TROUBLESHOOTING.md#L623-L694)