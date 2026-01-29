# LANrage Roadmap

## Phase 0: Prototype (Current)
**Goal**: Prove the concept works

- [x] Project structure
- [x] Basic API server
- [x] Web UI mockup
- [x] Configuration system
- [ ] WireGuard interface creation
- [ ] Key generation and management
- [ ] Local party creation (no networking)

**Timeline**: 1-2 weeks

## Phase 1: Local P2P
**Goal**: Two computers on same network can connect

- [ ] WireGuard peer configuration
- [ ] Direct P2P connection
- [ ] Latency measurement
- [ ] Party join/leave
- [ ] Basic status monitoring

**Timeline**: 2-3 weeks

## Phase 2: NAT Traversal
**Goal**: Connect across the internet

- [ ] STUN implementation
- [ ] UDP hole punching
- [ ] Connection type detection
- [ ] Automatic fallback logic
- [ ] First relay node (Oracle VPS)

**Timeline**: 3-4 weeks

## Phase 3: Control Plane
**Goal**: Centralized peer discovery

- [ ] Control server (Go/Rust)
- [ ] Peer registration
- [ ] Party discovery
- [ ] Key exchange
- [ ] Relay coordination

**Timeline**: 4-6 weeks

## Phase 4: Game Features
**Goal**: Actually works with games

- [ ] Broadcast emulation
- [ ] Multicast support
- [ ] Game detection
- [ ] Protocol optimization
- [ ] Test with 10+ popular games

**Timeline**: 4-6 weeks

## Phase 5: Polish
**Goal**: Production-ready

- [ ] Installer (Windows/Linux)
- [ ] Auto-updates
- [ ] Error handling
- [ ] Logging and diagnostics
- [ ] Performance tuning

**Timeline**: 3-4 weeks

## Phase 6: Scale
**Goal**: Handle real users

- [ ] Multiple relay nodes
- [ ] Anycast routing
- [ ] Geographic distribution
- [ ] Monitoring dashboard
- [ ] Usage analytics

**Timeline**: 4-6 weeks

## Phase 7: Mobile
**Goal**: Android support

- [ ] Android app
- [ ] Mobile-optimized UI
- [ ] Battery optimization
- [ ] Background service

**Timeline**: 6-8 weeks

## Phase 8: Advanced Features
**Goal**: Beyond basic VPN

- [ ] Integrated voice chat
- [ ] Screen sharing
- [ ] Game library integration
- [ ] Clan servers
- [ ] Custom domains

**Timeline**: Ongoing

## Success Metrics

### Phase 1-2
- Successfully connect 2 peers
- <10ms latency overhead
- Works on Windows + Linux

### Phase 3-4
- 10+ concurrent parties
- Works with 5+ games
- <15ms latency overhead

### Phase 5-6
- 100+ active users
- 99% uptime
- <20ms average latency

### Phase 7-8
- 1000+ active users
- Mobile app in beta
- Community feedback positive

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
