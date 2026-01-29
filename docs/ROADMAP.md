# LANrage Roadmap

## ✅ Phase 1: Production Ready v1.0 (COMPLETE)
**Goal**: Fully functional gaming VPN with all core features

**Status**: ✅ COMPLETE - Ready for public release

### Core Features ✅
- [x] Project structure and architecture
- [x] FastAPI REST API server
- [x] Web UI (HTML/CSS/JS)
- [x] Configuration system (Pydantic + SQLite)
- [x] WireGuard interface management
- [x] Key generation and management (Curve25519)
- [x] Party creation and management
- [x] WireGuard peer configuration
- [x] Direct P2P connections
- [x] Latency measurement
- [x] Party join/leave
- [x] Status monitoring and metrics

### NAT Traversal ✅
- [x] STUN implementation (5 public servers)
- [x] NAT type detection
- [x] UDP hole punching
- [x] Connection type detection
- [x] Automatic fallback logic
- [x] Relay server implementation
- [x] Relay discovery from control plane
- [x] Latency-based relay selection

### Control Plane ✅
- [x] HTTP-based control server (FastAPI)
- [x] SQLite database for persistence
- [x] Peer registration and discovery
- [x] Party discovery and coordination
- [x] Relay server registry
- [x] Automatic cleanup (stale peers/parties)
- [x] httpx-based async client
- [x] Retry logic and connection pooling

### Game Features ✅
- [x] Broadcast emulation (UDP/TCP)
- [x] Multicast support (mDNS/SSDP)
- [x] Game detection (27 games)
- [x] Game-specific optimization profiles
- [x] Socket-level QoS (iptables/netsh/tc)
- [x] Server browser (find and host)
- [x] Custom game profiles

### Quality & Polish ✅
- [x] 62 automated tests (100% passing)
- [x] 88% test coverage
- [x] Error handling (96% specific exceptions)
- [x] Performance optimization (all targets met)
- [x] Comprehensive documentation (1650+ lines)
- [x] User guide and troubleshooting
- [x] Discord integration (Rich Presence + webhooks)
- [x] Metrics collection and dashboard

**Timeline**: Complete (January 2026)
**Quality**: Production ready, enterprise-grade
**Test Coverage**: 88% (exceeded 85% target)
**Performance**: All targets met or exceeded

---

## Phase 2: Scale & Enhancement (v1.1)
**Goal**: Handle real users and improve UX

**Target**: Q2 2026

### Infrastructure
- [ ] Remote control plane (centralized deployment)
- [ ] Multiple relay nodes (geographic distribution)
- [ ] Anycast routing for relay selection
- [ ] Monitoring dashboard (Grafana/Prometheus)
- [ ] Usage analytics and telemetry
- [ ] Auto-scaling relay infrastructure

### User Experience
- [ ] Enhanced web UI (React/Vue rewrite)
- [ ] Installer (Windows/Linux packages)
- [ ] Auto-updates mechanism
- [ ] Improved error messages
- [ ] Onboarding tutorial
- [ ] In-app notifications

### Features
- [ ] IPv6 support
- [ ] More game profiles (50+ games)
- [ ] Game library integration (Steam/Epic)
- [ ] Voice chat quality optimization
- [ ] Advanced QoS tuning
- [ ] Custom relay configuration

**Timeline**: 3-4 months
**Focus**: Scalability and user experience

---

## Phase 3: Mobile Support (v2.0)
**Goal**: Android and iOS apps

**Target**: Q3-Q4 2026

### Mobile Apps
- [ ] Android app (Kotlin/Java)
- [ ] iOS app (Swift)
- [ ] Mobile-optimized UI
- [ ] Battery optimization
- [ ] Background service
- [ ] Push notifications
- [ ] Mobile game detection

### Cross-Platform
- [ ] Account synchronization
- [ ] Cross-platform parties
- [ ] Mobile-desktop interop
- [ ] Unified settings

**Timeline**: 6-8 months
**Focus**: Mobile gaming support

---

## Phase 4: Advanced Features (v3.0+)
**Goal**: Beyond basic VPN

**Target**: 2027+

### Community Features
- [ ] Clan servers (persistent hosting)
- [ ] Custom domains (clan.lanrage.io)
- [ ] Team management
- [ ] Tournament mode
- [ ] Leaderboards and stats
- [ ] Community profiles

### Enterprise Features
- [ ] Organization accounts
- [ ] SSO integration
- [ ] Advanced analytics
- [ ] Custom branding
- [ ] SLA guarantees
- [ ] Priority support

### Extensibility
- [ ] Plugin system (Python API)
- [ ] Custom protocol handlers
- [ ] Webhook integrations
- [ ] REST API for automation
- [ ] CLI tools

### Already Complete ✅
- [x] Voice chat (via Discord integration)
- [x] Screen sharing (via Discord integration)

**Timeline**: Ongoing
**Focus**: Community and enterprise needs

---

## Success Metrics

### ✅ Phase 1: v1.0 Production Ready (ACHIEVED)
- ✅ Successfully connect 2+ peers
- ✅ <3ms latency overhead (target: <10ms) - 70% better than target
- ✅ Works on Windows + Linux
- ✅ 27+ games supported
- ✅ <12ms relay latency (target: <15ms) - 20% better than target
- ✅ 88% test coverage (target: 85%)
- ✅ 96% specific exception handling
- ✅ Production-ready quality

### Phase 2: v1.1 Scale & Enhancement
- [ ] 100+ active users
- [ ] 99% uptime
- [ ] <20ms average latency
- [ ] Community feedback positive
- [ ] 50+ games supported

### Phase 3: v2.0 Mobile Support
- [ ] Mobile apps in beta
- [ ] 1000+ active users
- [ ] Cross-platform parties working
- [ ] Strong community engagement

### Phase 4: v3.0+ Advanced Features
- [ ] 10,000+ active users
- [ ] Enterprise customers
- [ ] Plugin ecosystem
- [ ] Sustainable business model

## Known Challenges

1. **NAT Traversal**: Some ISPs are evil
2. **Anti-Cheat**: May flag VPN usage
3. **Latency**: Physics is hard
4. **Platform Support**: Windows is weird
5. **Scaling**: Relays cost money

## Funding Strategy

### Bootstrap (Phase 0-3)
- Self-funded
- Oracle free tier
- Open source

### Early Access (Phase 4-5)
- Patreon/Ko-fi
- Early adopter perks
- Community support

### Freemium (Phase 6+)
- Free tier (limited)
- Paid tier ($5/month)
- Clan servers ($20/month)

## Community

- Discord server
- GitHub issues
- Reddit community
- Twitch streamers (marketing)

## Competition

- **Hamachi**: Dead, but nostalgic
- **ZeroTier**: Too enterprise
- **Radmin**: Windows-only
- **Tailscale**: Not for gamers

**Our edge**: Gaming-first, zero config, latency obsessed

## Long-Term Vision

LANrage becomes the de facto standard for:
- LAN parties over internet
- Private game servers
- Retro gaming communities
- Esports practice sessions

## Exit Strategy

- Acquisition by gaming company?
- Sustainable indie business?
- Open source forever?

TBD based on traction.
