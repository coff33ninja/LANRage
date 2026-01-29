# Troubleshooting Guide

Common issues and solutions for LANrage.

## Troubleshooting Flowcharts

Visual guides for diagnosing common issues. Follow the flowchart paths to quickly identify and resolve problems.

### Connection Issues Flowchart

```mermaid
flowchart TD
    Start([Connection Problem]) --> CanCreate{Can create<br/>party?}
    
    CanCreate -->|No| CheckInternet[Check internet<br/>connection]
    CheckInternet --> Internet{Internet<br/>working?}
    Internet -->|No| FixInternet[Fix internet<br/>connection]
    Internet -->|Yes| CheckFirewall[Check firewall<br/>settings]
    CheckFirewall --> AllowLANrage[Allow LANrage<br/>through firewall]
    
    CanCreate -->|Yes| CanJoin{Can join<br/>party?}
    CanJoin -->|No| CheckPartyID[Verify Party ID<br/>is correct]
    CheckPartyID --> HostRunning{Is host<br/>running?}
    HostRunning -->|No| StartHost[Ask host to<br/>start LANrage]
    HostRunning -->|Yes| RecreateParty[Recreate party<br/>with new ID]
    
    CanJoin -->|Yes| PeerConnect{Can connect<br/>to peers?}
    PeerConnect -->|No| CheckNAT[Check NAT type<br/>in web UI]
    CheckNAT --> NATType{NAT type?}
    NATType -->|Open/Moderate| CheckPorts[Check UDP port<br/>51820 open]
    NATType -->|Strict/Symmetric| UseRelay[Use relay server<br/>automatic fallback]
    CheckPorts --> OpenPorts[Open firewall<br/>for UDP 51820]
    
    PeerConnect -->|Yes| HighLatency{High<br/>latency?}
    HighLatency -->|Yes| CheckConnection[Check connection<br/>type in UI]
    CheckConnection --> ConnType{Direct or<br/>Relayed?}
    ConnType -->|Direct| OptimizeNetwork[Optimize network:<br/>- Close bandwidth apps<br/>- Use wired connection<br/>- Check for congestion]
    ConnType -->|Relayed| TryDirect[Try forcing<br/>direct connection]
    
    HighLatency -->|No| Success([✅ Connected<br/>Successfully])
    
    FixInternet --> Start
    AllowLANrage --> Start
    StartHost --> CanJoin
    RecreateParty --> CanJoin
    UseRelay --> PeerConnect
    OpenPorts --> PeerConnect
    OptimizeNetwork --> Success
    TryDirect --> Success
```

### Game Detection Flowchart

```mermaid
flowchart TD
    Start([Game Not Detected]) --> CheckSupported{Is game<br/>supported?}
    
    CheckSupported -->|Not Sure| CheckProfiles[Check game_profiles/<br/>directory]
    CheckProfiles --> InProfiles{Game in<br/>profiles?}
    
    CheckSupported -->|Yes| GameRunning{Is game<br/>running?}
    InProfiles -->|Yes| GameRunning
    
    GameRunning -->|No| StartGame[Start the game<br/>first]
    StartGame --> Detected{Game<br/>detected?}
    
    GameRunning -->|Yes| CheckProcess[Check process name<br/>matches profile]
    CheckProcess --> ProcessMatch{Process<br/>matches?}
    
    ProcessMatch -->|No| UpdateProfile[Update profile with<br/>correct process name]
    UpdateProfile --> RestartLANrage[Restart LANrage]
    
    ProcessMatch -->|Yes| Detected
    
    InProfiles -->|No| CreateCustom[Create custom<br/>profile]
    CreateCustom --> CustomSteps[1. Create JSON in<br/>game_profiles/custom/<br/>2. Add game details<br/>3. Restart LANrage]
    CustomSteps --> Detected
    
    Detected -->|Yes| Success([✅ Game Detected<br/>& Optimized])
    Detected -->|No| RequestSupport[Request game support<br/>on GitHub]
    RequestSupport --> UseGeneric[Use generic mode<br/>for now]
    
    UseGeneric --> ManualConfig[Manual configuration:<br/>- Set ports manually<br/>- Enable broadcast if needed<br/>- Adjust MTU if needed]
    ManualConfig --> Success
```

### High Latency Troubleshooting

```mermaid
flowchart TD
    Start([High Latency]) --> Measure[Measure latency<br/>in Statistics]
    Measure --> LatencyLevel{Latency<br/>level?}
    
    LatencyLevel -->|<10ms| Normal([✅ Normal<br/>for gaming])
    LatencyLevel -->|10-50ms| Acceptable[Acceptable but<br/>can improve]
    LatencyLevel -->|>50ms| Problem[Problematic<br/>needs fixing]
    
    Acceptable --> CheckType1[Check connection<br/>type in UI]
    Problem --> CheckType2[Check connection<br/>type in UI]
    
    CheckType1 --> ConnType1{Connection<br/>type?}
    CheckType2 --> ConnType2{Connection<br/>type?}
    
    ConnType1 -->|Direct| DirectOpt[Direct connection<br/>optimization]
    ConnType2 -->|Direct| DirectOpt
    
    DirectOpt --> CheckBase[Check base latency<br/>ping peer's real IP]
    CheckBase --> BaseHigh{Base latency<br/>high?}
    
    BaseHigh -->|Yes| NetworkIssue[Network issue:<br/>- ISP problem<br/>- Distance too far<br/>- Network congestion]
    NetworkIssue --> NetworkFix[Fix network:<br/>- Contact ISP<br/>- Use closer peers<br/>- Reduce congestion]
    
    BaseHigh -->|No| LANrageOverhead[LANrage overhead<br/>issue]
    LANrageOverhead --> ReduceOverhead[Reduce overhead:<br/>- Update LANrage<br/>- Optimize settings<br/>- Check CPU usage]
    
    ConnType1 -->|Relayed| RelayOpt[Relay connection<br/>optimization]
    ConnType2 -->|Relayed| RelayOpt
    
    RelayOpt --> WhyRelay{Why using<br/>relay?}
    WhyRelay -->|NAT issues| FixNAT[Fix NAT:<br/>- Open ports<br/>- Enable UPnP<br/>- DMZ host]
    WhyRelay -->|Firewall| FixFirewall[Fix firewall:<br/>- Allow UDP 51820<br/>- Disable strict rules]
    WhyRelay -->|Distance| CloserRelay[Use closer<br/>relay server]
    
    FixNAT --> TryDirect[Try direct<br/>connection]
    FixFirewall --> TryDirect
    CloserRelay --> CheckRelay[Check relay<br/>selection in UI]
    
    TryDirect --> Success([✅ Latency<br/>Improved])
    CheckRelay --> Success
    NetworkFix --> Success
    ReduceOverhead --> Success
```

### Relay Server Selection

```mermaid
flowchart TD
    Start([Need Relay Server]) --> AutoSelect{Auto-select<br/>enabled?}
    
    AutoSelect -->|Yes| Measure[Measure latency to<br/>all available relays]
    Measure --> SelectBest[Select relay with<br/>lowest latency]
    SelectBest --> TestConnection[Test connection<br/>through relay]
    
    AutoSelect -->|No| ManualSelect[Manual relay<br/>selection]
    ManualSelect --> ChooseRelay[Choose relay from<br/>available list]
    ChooseRelay --> TestConnection
    
    TestConnection --> Working{Relay<br/>working?}
    
    Working -->|No| CheckRelay[Check relay status]
    CheckRelay --> RelayStatus{Relay<br/>online?}
    RelayStatus -->|No| TryAnother[Try another<br/>relay server]
    RelayStatus -->|Yes| CheckFirewall[Check firewall<br/>allows relay]
    CheckFirewall --> TryAnother
    
    TryAnother --> Measure
    
    Working -->|Yes| CheckLatency{Latency<br/>acceptable?}
    CheckLatency -->|No| TryCloser[Try geographically<br/>closer relay]
    TryCloser --> Measure
    
    CheckLatency -->|Yes| Success([✅ Relay<br/>Connected])
    
    Success --> Monitor[Monitor connection<br/>quality]
    Monitor --> QualityCheck{Quality<br/>degraded?}
    QualityCheck -->|Yes| AutoSwitch[Auto-switch to<br/>better relay]
    AutoSwitch --> Measure
    QualityCheck -->|No| Monitor
```

### WireGuard Interface Issues

```mermaid
flowchart TD
    Start([WireGuard Interface<br/>Problem]) --> CheckInstalled{WireGuard<br/>installed?}
    
    CheckInstalled -->|No| Install[Install WireGuard]
    Install --> InstallOS{Operating<br/>System?}
    InstallOS -->|Windows| InstallWin[Download from<br/>wireguard.com]
    InstallOS -->|Linux| InstallLinux[sudo apt install<br/>wireguard]
    InstallOS -->|Mac| InstallMac[brew install<br/>wireguard-tools]
    
    InstallWin --> Verify
    InstallLinux --> Verify
    InstallMac --> Verify
    
    CheckInstalled -->|Yes| CheckPerms{Have admin/<br/>root perms?}
    
    CheckPerms -->|No| GetPerms[Run with elevated<br/>privileges]
    GetPerms --> PermsOS{Operating<br/>System?}
    PermsOS -->|Windows| RunAsAdmin[Right-click<br/>Run as Administrator]
    PermsOS -->|Linux/Mac| RunSudo[Run with sudo]
    
    RunAsAdmin --> CheckPerms
    RunSudo --> CheckPerms
    
    CheckPerms -->|Yes| CreateInterface[Try creating<br/>interface]
    CreateInterface --> Created{Interface<br/>created?}
    
    Created -->|No| CheckError[Check error<br/>message]
    CheckError --> ErrorType{Error<br/>type?}
    
    ErrorType -->|Already exists| DeleteOld[Delete old interface:<br/>Windows: netsh interface delete<br/>Linux: ip link delete]
    ErrorType -->|Port in use| ChangePort[Change WireGuard<br/>port in settings]
    ErrorType -->|Permission denied| GetPerms
    ErrorType -->|Other| CheckLogs[Check logs for<br/>details]
    
    DeleteOld --> CreateInterface
    ChangePort --> CreateInterface
    CheckLogs --> ReportIssue[Report issue<br/>on GitHub]
    
    Created -->|Yes| TestInterface[Test interface]
    TestInterface --> Working{Interface<br/>working?}
    
    Working -->|No| CheckConfig[Check interface<br/>configuration]
    CheckConfig --> ConfigOK{Config<br/>valid?}
    ConfigOK -->|No| FixConfig[Fix configuration:<br/>- Check IP range<br/>- Verify keys<br/>- Check MTU]
    ConfigOK -->|Yes| RestartInterface[Restart interface]
    
    FixConfig --> CreateInterface
    RestartInterface --> Working
    
    Working -->|Yes| Success([✅ Interface<br/>Working])
    
    Verify --> CheckInstalled
```

## Quick Diagnostics

Run these checks before diving into specific issues:

```bash
# 1. Check LANrage status
curl http://localhost:8666/api/status

# 2. Check WireGuard interface (Windows)
netsh interface show interface name="lanrage0"

# 3. Check WireGuard interface (Linux/Mac)
ip addr show lanrage0

# 4. Check logs
type %USERPROFILE%\.lanrage\network.log  # Windows
cat ~/.lanrage/network.log               # Linux/Mac
```

---

## Installation Issues

### WireGuard Not Found

**Symptoms:**
```
❌ WireGuard not found
Please install WireGuard first
```

**Solutions:**

**Windows:**
1. Download from https://www.wireguard.com/install/
2. Run installer
3. Restart LANrage

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install wireguard
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install wireguard-tools
```

**Verify:**
```bash
wg --version
```

---

### Permission Denied

**Symptoms:**
```
❌ Permission denied
Failed to create interface
```

**Cause:** LANrage needs admin/root privileges for network interfaces

**Solutions:**

**Windows:**
- Right-click `lanrage.py` → "Run as Administrator"
- Or run from elevated PowerShell

**Linux/Mac:**
```bash
sudo python lanrage.py
```

**Alternative (Linux):**
```bash
sudo setcap cap_net_admin+ep $(which python3)
```

---

### Python Version Error

**Symptoms:**
```
❌ Python 3.12+ required
Current version: 3.10.x
```

**Solutions:**

**Windows:**
1. Download Python 3.12+ from python.org
2. Install with "Add to PATH" checked
3. Verify: `python --version`

**Linux:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12
python3.12 lanrage.py
```

**Mac:**
```bash
brew install python@3.12
```

---

### Dependencies Installation Failed

**Solutions:**

1. **Update uv:**
   ```bash
   pip install --upgrade uv
   ```

2. **Install with verbose output:**
   ```bash
   uv pip install -r requirements.txt -v
   ```

3. **Check internet connection:**
   ```bash
   ping pypi.org
   ```

4. **Install build tools (if needed):**
   
   **Windows:** Install Visual Studio Build Tools
   
   **Linux:**
   ```bash
   sudo apt install build-essential python3-dev
   ```

---

## Connection Issues

### Cannot Create Party

**Symptoms:**
```
⚠️ Failed to create party
Connection to control server failed
```

**Solutions:**

1. **Check internet:**
   ```bash
   ping 8.8.8.8
   ```

2. **Check firewall:**
   - Windows: Allow LANrage through Windows Firewall
   - Linux: Check iptables/ufw rules

3. **Use local mode (temporary):**
   Edit `.env`:
   ```bash
   LANRAGE_CONTROL_MODE=local
   ```

---

### Cannot Join Party

**Symptoms:**
```
⚠️ Failed to join party
Party not found: abc123xyz
```

**Solutions:**

1. **Verify Party ID:**
   - Double-check with host
   - Party IDs are case-sensitive
   - No spaces or special characters

2. **Check host status:**
   - Ask host if LANrage is still running
   - Host should see party in web UI

3. **Try recreating party:**
   - Host creates new party
   - Use new Party ID

---

### Peer Connection Failed

**Symptoms:**
```
⚠️ Failed to connect to peer
Connection timeout
```

**Solutions:**

1. **Check NAT type:**
   LANrage shows NAT type in web UI
   - Open NAT: Should work
   - Moderate NAT: Usually works
   - Strict/Symmetric NAT: May need relay

2. **Check firewall:**
   Allow UDP port 51820:
   
   **Windows:**
   ```powershell
   New-NetFirewallRule -DisplayName "LANrage" -Direction Inbound -Protocol UDP -LocalPort 51820 -Action Allow
   ```

   **Linux:**
   ```bash
   sudo ufw allow 51820/udp
   ```

3. **Try different network:**
   - Mobile hotspot
   - Different WiFi
   - Wired connection

---

### High Latency

**Symptoms:**
- Ping >50ms to nearby peers
- Laggy gameplay
- Delayed responses

**Diagnosis:**

1. **Check connection type:**
   Web UI → Statistics → Connection Type
   - Direct: Should be <5ms overhead
   - Relayed: Should be <15ms overhead

2. **Check base latency:**
   ```bash
   ping <peer-real-ip>
   ```

3. **Calculate overhead:**
   ```
   Total Latency = Base Latency + LANrage Overhead
   ```

**Solutions:**

1. **If using relay:**
   - Try forcing direct connection
   - Check if both NATs allow P2P
   - Use closer relay server

2. **If direct connection:**
   - Check for network congestion
   - Close bandwidth-heavy apps
   - Use wired connection

3. **Optimize game settings:**
   - Lower graphics settings
   - Disable background downloads
   - Close streaming apps

---

### Packet Loss

**Symptoms:**
- Stuttering gameplay
- Disconnections
- "Connection lost" messages

**Diagnosis:**

Check packet loss in Statistics dashboard:
- <1%: Normal
- 1-5%: Noticeable
- >5%: Problematic

**Solutions:**

1. **Check network quality:**
   ```bash
   ping -t <peer-ip>  # Windows (continuous)
   ping <peer-ip>     # Linux/Mac
   ```

2. **Check WiFi signal:**
   - Move closer to router
   - Use 5GHz band if available
   - Switch to wired connection

3. **Reduce network load:**
   - Pause downloads
   - Close streaming services
   - Limit other devices on network

---

## Game-Specific Issues

### Game Not Detected

**Symptoms:**
```
ℹ️ No game detected
Running in generic mode
```

**Solutions:**

1. **Check supported games:**
   See `game_profiles/` directory

2. **Create custom profile:**
   Create `game_profiles/custom/mygame.json`:
   ```json
   {
     "name": "My Game",
     "process_names": ["mygame.exe", "mygame"],
     "broadcast_ports": [7777],
     "multicast_groups": [],
     "keepalive": 25,
     "mtu": 1420
   }
   ```

3. **Request game support:**
   Open GitHub issue with game details

---

### Minecraft: Cannot See LAN World

**Solutions:**

1. **Check broadcast emulation:**
   Web UI → Settings → Broadcast should be "Enabled"

2. **Verify virtual IPs:**
   All players should have 10.66.0.x addresses

3. **Check Minecraft version:**
   All players must use same version

4. **Manual connection:**
   - Get host's virtual IP from LANrage
   - In Minecraft: Direct Connect
   - Enter: `10.66.0.2:25565` (host's virtual IP)

---

### Terraria: Connection Failed

**Solutions:**

1. **Use virtual IP:**
   Connect to host's virtual IP (10.66.0.x), not real IP

2. **Check port:**
   Default Terraria port is 7777

3. **Verify server is running:**
   Host should see "Server started" in Terraria

---

### Stardew Valley: Cabin Not Available

**Solutions:**

1. **Build cabins first:**
   Host must build cabins on farm before friends can join

2. **Check cabin limit:**
   Max 3 friends (4 players total)

3. **Use invite code:**
   - Host: Get invite code from game
   - Friends: Use invite code to join

---

## Performance Issues

### High CPU Usage

**Symptoms:**
- LANrage using >20% CPU
- System slowdown
- Fan noise

**Solutions:**

1. **Check metrics collection:**
   Reduce collection frequency in settings

2. **Disable unused features:**
   - Discord integration (if not used)
   - Server browser (if not hosting)
   - Metrics collection (if not needed)

3. **Update LANrage:**
   Newer versions have performance improvements

4. **Restart LANrage:**
   Fresh start clears accumulated data

---

### High Memory Usage

**Symptoms:**
- LANrage using >200MB RAM
- System running out of memory

**Solutions:**

1. **Check metrics history:**
   Metrics are stored in memory
   - Reduce history size in settings
   - Clear old metrics

2. **Check server browser:**
   Large server lists use memory
   - Clear old servers
   - Reduce refresh rate

3. **Restart LANrage:**
   Fresh start clears accumulated data

---

### Slow Web UI

**Solutions:**

1. **Check browser:**
   - Use modern browser (Chrome, Firefox, Edge)
   - Clear browser cache
   - Disable extensions

2. **Check API response:**
   ```bash
   curl http://localhost:8666/api/status
   ```
   Should respond in <100ms

3. **Reduce update frequency:**
   Web UI polls API every 2 seconds
   - Increase interval in settings
   - Or disable auto-refresh

---

## Discord Integration Issues

### Rich Presence Not Working

**Solutions:**

1. **Check Discord is running:**
   Discord must be running before starting LANrage

2. **Check pypresence installed:**
   ```bash
   uv pip list | grep pypresence
   ```

3. **Restart both:**
   - Close Discord
   - Stop LANrage
   - Start Discord
   - Start LANrage

4. **Check Discord settings:**
   Settings → Activity Status → "Display current activity" enabled

---

### Webhook Not Sending

**Solutions:**

1. **Verify webhook URL:**
   - Should start with `https://discord.com/api/webhooks/`
   - Copy entire URL including token

2. **Check webhook permissions:**
   - Webhook must have "Send Messages" permission
   - Channel must allow webhooks

3. **Test webhook:**
   ```bash
   curl -X POST <webhook-url> \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message"}'
   ```

---

## Advanced Troubleshooting

### Enable Debug Logging

Add to `.env`:
```bash
LANRAGE_LOG_LEVEL=DEBUG
```

Restart LANrage. Check logs:
```bash
tail -f ~/.lanrage/network.log  # Linux/Mac
type %USERPROFILE%\.lanrage\network.log  # Windows
```

---

### Check WireGuard Status

```bash
wg show lanrage0
```

Should show:
- Interface public key
- Listening port
- Peers (if connected)
- Latest handshake times

---

### Reset LANrage

Complete reset (loses all data):

```bash
# Stop LANrage
# Delete config directory
rm -rf ~/.lanrage  # Linux/Mac
rmdir /s %USERPROFILE%\.lanrage  # Windows

# Restart LANrage
python lanrage.py
```

---

### Collect Diagnostic Info

For bug reports:

```bash
# 1. LANrage version
python lanrage.py --version

# 2. System info
python -c "import platform; print(platform.platform())"

# 3. WireGuard version
wg --version

# 4. Network interfaces
ip addr  # Linux/Mac
ipconfig  # Windows

# 5. Recent logs
tail -100 ~/.lanrage/network.log

# 6. Current status
curl http://localhost:8666/api/status
```

---

## Common Error Messages

### "Interface already exists"

**Solution:**
```bash
# Windows
netsh interface delete interface name="lanrage0"

# Linux
sudo ip link delete lanrage0
```

---

### "Address already in use"

**Solution:**
```bash
# Find what's using port 8666
# Windows
netstat -ano | findstr :8666

# Linux/Mac
lsof -i :8666

# Use different port
python lanrage.py --port 9000
```

---

### "Handshake timeout"

**Solutions:**
1. Check firewall allows UDP 51820
2. Verify peer's public key is correct
3. Check network connectivity
4. Try different endpoint

---

### "Invalid party ID"

**Solutions:**
- Party IDs are alphanumeric
- No spaces or special characters
- Case-sensitive
- Get fresh ID from host

---

## Getting Help

### Before Asking

1. Check this troubleshooting guide
2. Search GitHub issues
3. Check documentation
4. Try basic solutions (restart, update, etc.)

### When Asking

Include:
- LANrage version
- Operating system
- Error messages (exact text)
- Steps to reproduce
- What you've already tried
- Diagnostic info (see above)

### Where to Get Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Discord**: Real-time community support (coming soon)

---

## Still Having Issues?

If you've tried everything:

1. **Create GitHub Issue**: https://github.com/yourusername/lanrage/issues
2. **Include diagnostic info**
3. **Be patient**: Community volunteers will help
4. **Consider workarounds**: Local mode, different network, etc.

Remember: LANrage is open source and community-supported. Your detailed bug reports help make it better for everyone!
