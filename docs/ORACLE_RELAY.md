# Setting Up Your Oracle VPS as a Relay

Your 1 core / 1GB Oracle VPS is perfect for a LANrage relay node. Here's how to set it up.

## What is a Relay?

A relay is a stateless packet forwarder that helps peers connect when direct P2P fails (NAT hell). It:
- Forwards encrypted WireGuard packets
- Never decrypts traffic
- Requires minimal resources
- Can handle dozens of concurrent connections

## Setup Steps

### 1. Prepare the VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install WireGuard
sudo apt install wireguard -y

# Install Python 3.12
sudo apt install python3.12 python3.12-venv -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 2. Clone LANrage

```bash
git clone https://github.com/yourusername/lanrage.git
cd lanrage
```

### 3. Setup Relay Mode

```bash
# Run setup
python3.12 setup.py

# Activate venv
source .venv/bin/activate

# Configure as relay
cat > .env << EOF
LANRAGE_MODE=relay
LANRAGE_RELAY_IP=$(curl -s ifconfig.me)
LANRAGE_API_PORT=8666
EOF
```

### 4. Configure Firewall

```bash
# Allow WireGuard port
sudo ufw allow 51820/udp

# Allow API port (for monitoring)
sudo ufw allow 8666/tcp

# Enable firewall
sudo ufw enable
```

### 5. Run as Service

Create `/etc/systemd/system/lanrage-relay.service`:

```ini
[Unit]
Description=LANrage Relay Node
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/lanrage
Environment="PATH=/home/ubuntu/lanrage/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/lanrage/.venv/bin/python lanrage.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lanrage-relay
sudo systemctl start lanrage-relay
sudo systemctl status lanrage-relay
```

### 6. Monitor

```bash
# Check logs
sudo journalctl -u lanrage-relay -f

# Check status
curl http://localhost:8666/api
```

## Performance Tuning

For a 1 core / 1GB VPS:

```bash
# Optimize network stack
sudo sysctl -w net.core.rmem_max=2500000
sudo sysctl -w net.core.wmem_max=2500000
sudo sysctl -w net.ipv4.udp_mem="102400 873800 16777216"

# Make permanent
echo "net.core.rmem_max=2500000" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=2500000" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.udp_mem=102400 873800 16777216" | sudo tee -a /etc/sysctl.conf
```

## Expected Capacity

With 1 core / 1GB:
- ~50-100 concurrent connections
- ~500 Mbps throughput
- <5ms added latency
- ~500MB RAM usage

## Monitoring

Add to your relay:

```bash
# Install monitoring
uv pip install psutil

# Check resource usage
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%')"
```

## Security Notes

- Relay never sees unencrypted traffic
- No logs stored by default
- Minimal attack surface
- Auto-updates recommended

## Cost

Oracle Free Tier includes:
- 1 core / 1GB VPS (forever free)
- 10TB/month bandwidth
- Perfect for a relay node

## Next Steps

Once your relay is running:
1. Note the public IP
2. Add it to the control plane (TODO)
3. Clients will auto-discover it
4. Monitor via API endpoint
