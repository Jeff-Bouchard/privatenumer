# ENUM Backend Deployment Guide

## Quick Start (5 Minutes)

### 1. Prepare Raspberry Pi

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Verify Emercoin is running
emercoin-cli getinfo
```

If Emercoin is not installed, see [Emercoin Installation](#emercoin-installation) below.

### 2. Transfer Files

From your development machine:

```bash
# Option A: Direct copy
scp -r enum-server/ pi@raspberrypi.local:/home/pi/

# Option B: Git clone (if in repo)
ssh pi@raspberrypi.local
git clone https://github.com/your-repo/enum-server.git
cd enum-server
```

### 3. Run Setup

```bash
cd /home/pi/enum-server
chmod +x setup.sh
sudo ./setup.sh
```

The setup script will:
- Install Python dependencies
- Configure systemd service
- Start the backend
- Configure firewall

### 4. Verify Installation

```bash
# Check service status
systemctl status enum-backend

# Test health endpoint
curl http://localhost:8080/health

# View logs
journalctl -u enum-backend -n 20
```

### 5. Register Test Number

```bash
cd /home/pi/enum-server/examples
chmod +x register_enum.sh

# Edit phone number and SIP URI
nano register_enum.sh

# Run registration
./register_enum.sh
```

### 6. Configure Antisip

1. Open Antisip on Android
2. Go to: **Settings → Network → ENUM**
3. Set:
   - **ENUM Server**: `http://<raspberry-pi-ip>:8080/enum/lookup?number=`
   - **ENUM Domain**: `e164.arpa`
   - **Enable ENUM**: ✓

4. Test: Dial the registered number

---

## Emercoin Installation

If you don't have Emercoin installed:

### Pre-built Binaries (Recommended)

```bash
# Download Emercoin (check latest version at emercoin.com)
cd /tmp
wget https://emercoin.com/downloads/emercoin-0.7.0-arm-linux-gnueabihf.tar.gz

# Extract
tar -xzf emercoin-0.7.0-arm-linux-gnueabihf.tar.gz

# Install
sudo cp emercoin-0.7.0/bin/* /usr/local/bin/
sudo chmod +x /usr/local/bin/emercoin*

# Create data directory
mkdir -p ~/.emercoin
```

### Configure Emercoin

```bash
# Create config file
cat > ~/.emercoin/emercoin.conf << EOF
server=1
daemon=1
rpcuser=$(openssl rand -hex 16)
rpcpassword=$(openssl rand -hex 32)
rpcallowip=127.0.0.1
maxconnections=50
addnode=seed.emercoin.com
addnode=seed2.emercoin.com
EOF

chmod 600 ~/.emercoin/emercoin.conf
```

### Create Systemd Service

```bash
sudo tee /etc/systemd/system/emercoin.service > /dev/null << EOF
[Unit]
Description=Emercoin Node
After=network.target

[Service]
Type=forking
User=pi
Group=pi
WorkingDirectory=/home/pi
ExecStart=/usr/local/bin/emercoind -daemon -conf=/home/pi/.emercoin/emercoin.conf
ExecStop=/usr/local/bin/emercoin-cli stop
Restart=on-failure
RestartSec=30
StandardOutput=null
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable emercoin
sudo systemctl start emercoin
```

### Initial Sync

```bash
# Check sync progress
emercoin-cli getinfo

# You'll see:
# "blocks": <current>  - Your node
# Network is at ~1.5M blocks (as of 2024)

# Sync will take several hours on Raspberry Pi
# Monitor with:
watch -n 10 'emercoin-cli getinfo | grep blocks'
```

---

## Production Deployment

### SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (requires domain pointing to your Pi)
sudo certbot certonly --standalone -d enum.yourdomain.com

# Install NGINX
sudo apt install nginx

# Copy NGINX config
sudo cp nginx/enum-backend.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/enum-backend.conf /etc/nginx/sites-enabled/

# Edit config to match your domain
sudo nano /etc/nginx/sites-available/enum-backend.conf

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Dynamic DNS (for Home Network)

If your Raspberry Pi is on a home network without static IP:

```bash
# Install ddclient
sudo apt install ddclient

# Configure (example for DuckDNS)
sudo tee /etc/ddclient.conf > /dev/null << EOF
protocol=duckdns
use=web
web=checkip.dyndns.org
server=www.duckdns.org
login=your-domain
password=your-token
your-domain.duckdns.org
EOF

sudo systemctl restart ddclient
```

### Port Forwarding

On your router, forward:
- **Port 80** → Raspberry Pi (for Let's Encrypt)
- **Port 443** → Raspberry Pi (for HTTPS)
- **Port 8080** → Raspberry Pi (if not using NGINX)

### Security Hardening

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure for NGINX
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true
EOF

sudo systemctl restart fail2ban

# Disable SSH password auth (use keys only)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh

# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Kernel Hardening (Advanced)

> **⚠️ CRITICAL WARNING ⚠️**
>
> **THIS MODIFICATION WILL CAUSE YOUR SYSTEM TO BLOCK RATHER THAN PERFORM UNSECURE OPERATIONS**
>
> The system may block during boot or operation if insufficient entropy is available. Only apply this if you understand the implications and have alternative entropy sources configured (e.g., hardware RNG, haveged).

**Disable CPU Hardware RNG Trust:**

The `random.trust_cpu=off` parameter forces the kernel to NOT trust CPU-provided entropy from RDRAND/RDSEED instructions. This is a security measure against potential hardware backdoors in CPU random number generators.

```bash
# Edit GRUB configuration
sudo nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT:
GRUB_CMDLINE_LINUX_DEFAULT="quiet random.trust_cpu=off"

# Update GRUB
sudo update-grub

# Reboot required
sudo reboot
```

**Verify after reboot:**
```bash
cat /proc/cmdline | grep random.trust_cpu
dmesg | grep -i random
```

**Consequences:**
- ✅ **Security**: System will not trust potentially compromised CPU RNG
- ⚠️ **Blocking Behavior**: System WILL BLOCK if insufficient entropy available
- ⚠️ **Boot Time**: May significantly increase boot time while gathering entropy
- ⚠️ **Operation**: Random operations (TLS, SSH, key generation) may block

**Entropy Sources for This Project:**

This system uses **Gibson's Ultra-High Entropy PRNG** (`pyuheprng`) + **Emercoin Core's embedded RC4OK**.

```bash
# pyuheprng is already in requirements.txt and installed automatically
# during setup.sh execution

# Verify entropy pool (should maintain >3000 with pyuheprng + RC4OK)
cat /proc/sys/kernel/random/entropy_avail

# For generic systems without pyuheprng:
# sudo apt install haveged
# sudo systemctl enable haveged
```

**📖 For complete details, rollback procedures, monitoring, and additional kernel hardening, see:**
**[SECURITY_HARDENING.md](SECURITY_HARDENING.md)** - Full kernel hardening guide

---

## Backup & Recovery

### Backup Emercoin Wallet

```bash
# Backup wallet
emercoin-cli backupwallet /home/pi/backups/wallet-$(date +%F).dat

# Automated daily backup
echo "0 2 * * * /usr/local/bin/emercoin-cli backupwallet /home/pi/backups/wallet-\$(date +\%F).dat" | crontab -
```

### Backup ENUM Configuration

```bash
# Backup service config
sudo cp /etc/systemd/system/enum-backend.service ~/backups/

# Backup NGINX config
sudo cp /etc/nginx/sites-available/enum-backend.conf ~/backups/

# Backup application
tar -czf ~/backups/enum-server-$(date +%F).tar.gz /home/pi/enum-server
```

### Restore from Backup

```bash
# Stop service
sudo systemctl stop enum-backend emercoin

# Restore wallet
cp ~/backups/wallet-YYYY-MM-DD.dat ~/.emercoin/wallet.dat

# Restore application
tar -xzf ~/backups/enum-server-YYYY-MM-DD.tar.gz -C /

# Start services
sudo systemctl start emercoin enum-backend
```

---

## Monitoring

### Prometheus + Grafana

```bash
# Install Prometheus
sudo apt install prometheus

# Add ENUM backend metrics endpoint
# (requires adding prometheus_client to requirements.txt)

# Install Grafana
sudo apt install grafana

# Configure dashboard for:
# - ENUM lookup rate
# - Response times
# - Emercoin block height
# - System resources
```

### Simple Uptime Monitoring

```bash
# Create monitoring script
cat > ~/monitor_enum.sh << 'EOF'
#!/bin/bash
HEALTH=$(curl -s http://localhost:8080/health | jq -r '.status')
if [ "$HEALTH" != "healthy" ]; then
    echo "ENUM backend is down!" | mail -s "ENUM Alert" your@email.com
    sudo systemctl restart enum-backend
fi
EOF

chmod +x ~/monitor_enum.sh

# Run every 5 minutes
echo "*/5 * * * * /home/pi/monitor_enum.sh" | crontab -
```

---

## Scaling

### Multiple Instances (Load Balancing)

```nginx
# NGINX config with multiple backends
upstream enum_backends {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    location / {
        proxy_pass http://enum_backends;
    }
}
```

Run multiple instances:

```bash
python3 enum_backend.py --port 8080 &
python3 enum_backend.py --port 8081 &
python3 enum_backend.py --port 8082 &
```

### Caching Layer (Redis)

```bash
# Install Redis
sudo apt install redis-server

# Add to requirements.txt:
# redis==4.5.1
# flask-caching==2.0.2
```

Modify `enum_backend.py` to add caching:

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 3600
})

@app.route('/enum/lookup')
@cache.cached(query_string=True)
def enum_lookup():
    # ... existing code
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
journalctl -u enum-backend -n 100 --no-pager

# Common issues:
# 1. Port in use
sudo ss -tlnp | grep 8080
sudo kill <PID>

# 2. Emercoin not running
sudo systemctl status emercoin
sudo systemctl start emercoin

# 3. Permission issues
sudo chown -R pi:pi /home/pi/enum-server
```

### Slow ENUM Lookups

```bash
# Check Emercoin RPC latency
time emercoin-cli getinfo

# If slow:
# - Increase dbcache in emercoin.conf
# - Use SSD instead of SD card
# - Add caching layer
```

### High Memory Usage

```bash
# Monitor
htop

# Limit Emercoin memory
nano ~/.emercoin/emercoin.conf
# Add: dbcache=256

# Limit backend workers
# Use gunicorn with limited workers
```

---

## Testing

### Run Test Suite

```bash
cd /home/pi/enum-server
pip3 install requests
python3 test_enum.py
```

### Manual Tests

```bash
# Health check
curl http://localhost:8080/health

# ENUM lookup
curl "http://localhost:8080/enum/lookup?number=%2B1234567890"

# List all
curl http://localhost:8080/enum/list

# Load test (with Apache Bench)
sudo apt install apache2-utils
ab -n 1000 -c 10 "http://localhost:8080/health"
```

---

## Cost Analysis

### Hardware
- **Raspberry Pi 4 (4GB)**: $55
- **SD Card (64GB)**: $10
- **Case + Power**: $15
- **Total**: ~$80

### Operating Costs
- **Power**: 3W × 24h × 30 days × $0.12/kWh = **$0.26/month**
- **Bandwidth**: Negligible for home network
- **Domain (optional)**: $10-15/year

### Emercoin Costs
- **ENUM Registration**: ~0.01 EMC (~$0.10)
- **Annual Renewal**: ~0.005 EMC (~$0.05)
- **1000 numbers**: ~10 EMC (~$10/year)

**Total First Year**: ~$100 (hardware) + $1 (operation) = **$101**

**Ongoing**: < $2/month

---

## Next Steps

1. ✓ Install and configure ENUM backend
2. Register your phone numbers in Emercoin NVS
3. Configure Antisip clients
4. Set up monitoring and backups
5. (Optional) Add SSL/TLS for public access
6. (Optional) Integrate with existing VoIP infrastructure

## Support Resources

- **Emercoin Docs**: https://emercoin.com/documentation
- **RFC 6116 (ENUM)**: https://tools.ietf.org/html/rfc6116
- **Antisip Support**: https://antisip.com/support
- **This Project**: [GitHub/Support URL]
