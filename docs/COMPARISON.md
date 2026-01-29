# LANrage vs The Competition

## TL;DR

| Feature | LANrage | Hamachi | ZeroTier | Tailscale | Radmin |
|---------|---------|---------|----------|-----------|--------|
| **Gaming Focus** | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ⚠️ Partial |
| **Low Latency** | ✅ <5ms | ⚠️ 10-30ms | ⚠️ 10-30ms | ⚠️ 10-30ms | ✅ <10ms |
| **Zero Config** | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Partial | ✅ Yes |
| **Still Maintained** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Free Tier** | ✅ Yes | ⚠️ Limited | ✅ Yes | ✅ Yes | ❌ No |
| **Open Source** | ✅ Yes | ❌ No | ⚠️ Partial | ❌ No | ❌ No |
| **Broadcast Support** | ✅ Yes | ✅ Yes | ⚠️ Partial | ❌ No | ✅ Yes |
| **Mobile Support** | 🚧 Soon | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| **Self-Hostable** | ✅ Yes | ❌ No | ✅ Yes | ⚠️ Partial | ❌ No |

## Detailed Comparison

### Hamachi (LogMeIn)

**The OG gaming VPN**

**Pros**:
- Nostalgic
- Used to work great
- Simple UI

**Cons**:
- Basically abandoned
- Owned by LogMeIn (corporate hell)
- Free tier is 5 users (lol)
- Adds 20-30ms latency
- Windows-only (mostly)
- Closed source

**Verdict**: Dead. RIP 2004-2016.

---

### ZeroTier

**The enterprise mesh network**

**Pros**:
- Actually maintained
- Good documentation
- Self-hostable
- Cross-platform

**Cons**:
- Not gaming-focused
- Complex setup
- Enterprise jargon everywhere
- Latency not prioritized
- Broadcast support is meh

**Verdict**: Great for businesses, overkill for gaming.

---

### Tailscale

**The modern VPN darling**

**Pros**:
- Excellent UX
- WireGuard-based
- Well-funded
- Great documentation
- Cross-platform

**Cons**:
- Not gaming-focused
- Adds 10-20ms latency
- No broadcast emulation
- Closed source (mostly)
- Enterprise pricing model

**Verdict**: Best general VPN, but not for gamers.

---

### Radmin VPN

**The Russian contender**

**Pros**:
- Gaming-focused
- Low latency
- Free (with ads)
- Broadcast support

**Cons**:
- Windows-only
- Closed source
- Russian company (geopolitics)
- Limited features
- Sketchy privacy

**Verdict**: Works, but trust issues.

---

### LANrage

**The gamer's choice**

**Pros**:
- Gaming-first design
- Latency-obsessed
- Zero config
- Open source
- Self-hostable
- Free (for now)
- Broadcast emulation
- Game profiles

**Cons**:
- Early prototype
- Small team (solo)
- No mobile yet
- Limited testing

**Verdict**: The future (hopefully).

---

## Feature Deep Dive

### Latency

**Why it matters**: Every millisecond counts in gaming.

- **LANrage**: <5ms (direct), <15ms (relayed)
- **Hamachi**: 20-30ms
- **ZeroTier**: 10-30ms
- **Tailscale**: 10-20ms
- **Radmin**: <10ms

**Winner**: LANrage (when it works)

---

### Broadcast Support

**Why it matters**: Old LAN games use UDP broadcast for discovery.

- **LANrage**: Full emulation ✅
- **Hamachi**: Yes ✅
- **ZeroTier**: Partial ⚠️
- **Tailscale**: No ❌
- **Radmin**: Yes ✅

**Winner**: LANrage, Hamachi, Radmin

---

### Setup Complexity

**Why it matters**: Gamers want to play, not configure.

- **LANrage**: 1 click
- **Hamachi**: 2 clicks
- **ZeroTier**: 10 clicks + config file
- **Tailscale**: 5 clicks + account
- **Radmin**: 2 clicks

**Winner**: LANrage, Hamachi

---

### Privacy

**Why it matters**: Your gaming habits are your business.

- **LANrage**: No logging, open source
- **Hamachi**: LogMeIn owns your data
- **ZeroTier**: Minimal logging
- **Tailscale**: Some logging
- **Radmin**: Unknown (closed source)

**Winner**: LANrage

---

### Cost

**Why it matters**: Gamers are broke.

- **LANrage**: Free (for now)
- **Hamachi**: $49/year (5+ users)
- **ZeroTier**: Free (25 devices)
- **Tailscale**: Free (20 devices)
- **Radmin**: Free (with ads)

**Winner**: All free tiers are decent

---

## Use Case Recommendations

### "I just want to play Minecraft with friends"
→ **LANrage** or **Radmin**

### "I need a VPN for work and gaming"
→ **Tailscale**

### "I'm setting up a gaming community"
→ **LANrage** (self-hosted)

### "I need enterprise features"
→ **ZeroTier** or **Tailscale**

### "I'm nostalgic for 2006"
→ **Hamachi** (if it still works)

### "I don't trust anyone"
→ **LANrage** (self-hosted, open source)

---

## Technical Comparison

### Protocol

- **LANrage**: WireGuard
- **Hamachi**: Proprietary
- **ZeroTier**: Custom (Salsa20)
- **Tailscale**: WireGuard
- **Radmin**: Proprietary

**Winner**: WireGuard-based (LANrage, Tailscale)

---

### NAT Traversal

- **LANrage**: STUN + hole punching + relays
- **Hamachi**: Proprietary
- **ZeroTier**: Custom
- **Tailscale**: DERP relays
- **Radmin**: Proprietary

**Winner**: All work, different approaches

---

### Relay Infrastructure

- **LANrage**: Self-hostable + public relays
- **Hamachi**: LogMeIn servers
- **ZeroTier**: ZeroTier servers + self-host
- **Tailscale**: DERP servers
- **Radmin**: Radmin servers

**Winner**: LANrage (most flexible)

---

## The Honest Truth

### What LANrage Does Better

1. **Gaming focus** - Every decision optimized for gaming
2. **Latency** - Obsessively measured and minimized
3. **Open source** - No vendor lock-in
4. **Self-hostable** - Your data, your servers
5. **Broadcast emulation** - Old games just work

### What LANrage Does Worse

1. **Maturity** - Early prototype vs established products
2. **Platform support** - Windows/Linux only (for now)
3. **Documentation** - Still being written
4. **Community** - Small (for now)
5. **Enterprise features** - None (by design)

### What LANrage Will Never Do

1. **Enterprise features** - ACLs, SSO, compliance
2. **Mobile-first** - Desktop gaming is the focus
3. **Closed source** - Open source forever
4. **Ads** - Never
5. **Sell your data** - Never

---

## Migration Guide

### From Hamachi

1. Export your network list
2. Create LANrage party
3. Invite friends
4. Uninstall Hamachi
5. Never look back

### From ZeroTier

1. Note your network ID
2. Create LANrage party
3. Migrate peers
4. Keep ZeroTier for non-gaming

### From Tailscale

1. Export your tailnet
2. Create LANrage party
3. Use Tailscale for work
4. Use LANrage for gaming

---

## Conclusion

**Use LANrage if**:
- You're a gamer
- You care about latency
- You want zero config
- You value open source

**Use Tailscale if**:
- You need a general VPN
- You want enterprise features
- You don't mind 10-20ms latency

**Use ZeroTier if**:
- You're a network engineer
- You like complex configs
- You need SD-WAN features

**Use Radmin if**:
- You're on Windows
- You trust Russian software
- You don't mind ads

**Use Hamachi if**:
- You're stuck in 2006
- You enjoy pain
- You hate yourself

---

## FAQ

**Q: Why not just improve Tailscale?**
A: Different goals. Tailscale is for enterprises, LANrage is for gamers.

**Q: Why not contribute to ZeroTier?**
A: Too enterprise-focused. Gaming needs different priorities.

**Q: Is LANrage a Tailscale fork?**
A: No. Built from scratch with gaming in mind.

**Q: Will LANrage replace Tailscale?**
A: No. Different use cases. Use both if needed.

**Q: Why not just use a regular VPN?**
A: Regular VPNs don't do mesh networking or broadcast emulation.

**Q: Can I use LANrage for non-gaming?**
A: Sure, but Tailscale is better for that.
