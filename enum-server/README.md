# Privateness.network ENUM Backend - Technical Reference

## Decentralized VoIP Without DNS Infrastructure

RFC 6116-based ENUM implementation using **Emercoin's Name-Value Storage (NVS)** blockchain for decentralized telephone number to SIP URI mapping. This is Privateness.network's core technology for achieving **truly decentralized VoIP** - no DNS servers, no ENUM registrars, no ICANN, no centralized points of failure.

**Key Technologies:**

- **Emercoin NVS** - Blockchain-based key-value store replaces DNS
- **Gibson's pyuheprng** - Ultra-high entropy PRNG for cryptographic operations
- **Emercoin RC4OK** - Embedded entropy source for `random.trust_cpu=off` deployments
- **Flask REST API** - Lightweight bridge between Antisip and blockchain
- **Simplified NAPTR** - Optimized format for blockchain storage efficiency

## Architecture

```text
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Antisip   │──HTTP──→│ ENUM Backend │──RPC───→│  Emercoin   │
│   Android   │         │    Flask     │         │  NVS Chain  │
└─────────────┘         └──────────────┘         └─────────────┘
                              ↓
                         Parse NAPTR
                              ↓
                        Return SIP URI
```

## Components

### 1. **Emercoin NVS**

Blockchain-based key-value store that replaces traditional DNS:

- **Namespace**: `enum:` prefix
- **Key Format**: `enum:0.9.8.7.6.5.4.3.2.1.e164.arpa`
- **Value Format**: NAPTR records `"!^.*$!sip:user@domain!"|"!^.*$!sip:backup@domain!"`
- **TTL**: Configurable (default 365 days)
- **Cost**: ~0.01 EMC per record

### 2. **Flask Backend**

RESTful API server that bridges Antisip and Emercoin:

- Converts E.164 numbers to ENUM domains
- Queries Emercoin NVS via `emercoin-cli`
- Parses NAPTR records
- Returns SIP URIs in JSON format

### 3. **Antisip Integration**

VoIP client configuration:

- ENUM server URL: `http://raspberrypi-ip:8080/enum/lookup?number=`
- Automatic number resolution before placing calls

## Installation

### Prerequisites

- Raspberry Pi 3/4 with Raspberry Pi OS
- Running Emercoin full node (`emercoind`)
- Python 3.7+
- Root/sudo access

### Quick Setup

```bash
# 1. Clone or copy the enum-server directory to your Raspberry Pi
scp -r enum-server/ pi@raspberrypi:/home/pi/

# 2. SSH into Raspberry Pi
ssh pi@raspberrypi

# 3. Run setup script
cd /home/pi/enum-server
sudo chmod +x setup.sh
sudo ./setup.sh
```

The script will:

- Verify Emercoin installation
- Install Python dependencies
- Create systemd service
- Configure firewall
- Start the ENUM backend

### Manual Installation

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip

# Install Python packages
pip3 install -r requirements.txt

# Configure Emercoin paths in enum_backend.py
EMC_CLI_PATH = "/usr/local/bin/emercoin-cli"
EMC_DATADIR = "/home/pi/.emercoin"

# Run backend
python3 enum_backend.py --host 0.0.0.0 --port 8080
```

## API Reference

### Base URL

```text
http://<raspberry-pi-ip>:8080
```

### Endpoints

#### 1. Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "emercoin_connected": true,
  "blocks": 1234567,
  "version": "0.7.0"
}
```

#### 2. ENUM Lookup

```http
GET /enum/lookup?number=+1234567890
```

**Parameters:**

- `number` (required): E.164 formatted phone number

**Success Response (200):**

```json
{
  "status": "success",
  "phone_number": "+1234567890",
  "sip_uri": "sip:user@domain.com",
  "naptr_records": [
    {
      "pattern": "^.*$",
      "replacement": "sip:user@domain.com",
      "flags": "u",
      "order": 0,
      "preference": 10
    }
  ],
  "enum_domain": "0.9.8.7.6.5.4.3.2.1.e164.arpa",
  "expires_in": 12345,
  "owner_address": "EXxxx..."
}
```

**Not Found Response (404):**

```json
{
  "status": "not_found",
  "phone_number": "+1234567890"
}
```

#### 3. Register ENUM Record

```http
POST /enum/register
Content-Type: application/json
```

**Body:**

```json
{
  "phone_number": "+1234567890",
  "sip_uri": "sip:user@domain.com",
  "fallback_uris": ["sip:backup@domain.com"]
}
```

**Response (201):**

```json
{
  "status": "success",
  "nvs_key": "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa",
  "phone_number": "+1234567890",
  "enum_domain": "0.9.8.7.6.5.4.3.2.1.e164.arpa",
  "txid": "abc123...",
  "message": "ENUM record registered (requires confirmation)"
}
```

**Note:** Requires Emercoin wallet to be unlocked:

```bash
emercoin-cli walletpassphrase "your-passphrase" 300
```

#### 4. List All ENUM Records

```http
GET /enum/list
```

**Response:**

```json
{
  "status": "success",
  "count": 5,
  "records": [
    {
      "phone_number": "+1234567890",
      "sip_uri": "sip:user@domain.com",
      "nvs_key": "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa",
      "expires_in": 12345
    }
  ]
}
```

## Emercoin NVS Operations

### Register ENUM Record via CLI

```bash
# Format: name_new <name> <value> <days>
emercoin-cli name_new \
  "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  '"!^.*$!sip:user@domain.com!"' \
  365
```

### Multiple SIP URIs (Failover)

```bash
emercoin-cli name_new \
  "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  '"!^.*$!sip:primary@domain.com!"|"!^.*$!sip:backup@domain.com!"' \
  365
```

### Query Record

```bash
emercoin-cli name_show "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa"
```

### Update Record

```bash
emercoin-cli name_update \
  "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  '"!^.*$!sip:newuser@domain.com!"' \
  365
```

### Delete Record

```bash
emercoin-cli name_delete "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa"
```

## Antisip Configuration

### Step-by-Step

1. **Open Antisip App**
2. **Navigate to**: Settings → Advanced → ENUM
3. **Configure**:
   - Enable ENUM: ✓
   - ENUM Server: `http://<raspberry-pi-ip>:8080/enum/lookup?number=`
   - ENUM Domain: `e164.arpa`
4. **Test**: Make a call to a registered ENUM number

### Example

If you registered `+1234567890` → `sip:alice@example.com`:

1. In Antisip, dial: `+1234567890`
2. Antisip queries: `http://192.168.1.100:8080/enum/lookup?number=%2B1234567890`
3. Backend resolves: `enum:0.9.8.7.6.5.4.3.2.1.e164.arpa` → `sip:alice@example.com`
4. Antisip connects to: `sip:alice@example.com`

## Production Deployment

### HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d enum.yourdomain.com

# Install NGINX config
sudo cp nginx/enum-backend.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/enum-backend.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Security Hardening

1. **Firewall Rules**:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

1. **Emercoin RPC Security**:
Edit `~/.emercoin/emercoin.conf`:

```ini
rpcuser=your_secure_username
rpcpassword=your_secure_password
rpcallowip=127.0.0.1
```

1. **Rate Limiting** (nginx):

```nginx
limit_req_zone $binary_remote_addr zone=enum_limit:10m rate=10r/s;
limit_req zone=enum_limit burst=20 nodelay;
```

### Monitoring

```bash
# Service status
systemctl status enum-backend

# Real-time logs
journalctl -u enum-backend -f

# Emercoin sync status
emercoin-cli getinfo

# Check listening ports
ss -tlnp | grep 8080
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
journalctl -u enum-backend -n 100 --no-pager

# Common issues:
# 1. Emercoin not running
sudo systemctl status emercoin
sudo systemctl start emercoin

# 2. Port already in use
ss -tlnp | grep 8080
# Kill process if needed

# 3. Permission issues
sudo chown -R pi:pi /home/pi/enum-server
```

### ENUM Lookup Returns 404

```bash
# Verify record exists
emercoin-cli name_show "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa"

# Check if NVS is synced
emercoin-cli name_filter "enum:" 10

# Verify backend can reach Emercoin
curl http://localhost:8080/health
```

### Antisip Can't Reach Server

```bash
# Test from Antisip device
curl "http://<raspberry-pi-ip>:8080/health"

# Check firewall
sudo ufw status

# Verify server is listening on 0.0.0.0
ss -tlnp | grep 8080

# Check network connectivity
ping <raspberry-pi-ip>
```

## Performance Tuning

### For High-Load Scenarios

1. **Use Gunicorn** (WSGI server):

```bash
pip3 install gunicorn

gunicorn -w 4 -b 0.0.0.0:8080 enum_backend:app
```

1. **Enable Caching**:
Add Redis caching for frequent lookups:

```bash
pip3 install redis flask-caching
```

1. **Emercoin Optimization**:
Edit `emercoin.conf`:

```ini
dbcache=1024
maxconnections=125
```

## Cost Analysis

### Emercoin NVS Fees

- **New Registration**: ~0.001 EMC + network fee
- **Update**: 0.0001 EMC + network fee
- **Renewal**: 0.0001 EMC per 365 days
- **Delete**: 0.0001 EMC as name_update

**Example:**

- 1000 phone numbers
- 365-day registration
- Cost: ~10 EMC (~$5-10 USD at current rates)

### Infrastructure Costs

- **Raspberry Pi 4 (4GB)**: $55 one-time
- **Power**: ~3W = $0.50/month
- **Internet**: Existing connection
- **Total**: < $1/month operating cost

## Advanced Features

### Custom NAPTR Flags

```bash
# Voice-only
"!^.*$!sip:voice@domain.com!u"

# Video call
"!^.*$!sip:video@domain.com!v"

# Both
"!^.*$!sip:user@domain.com!uv"
```

### Geographic Routing

```bash
# US number
"enum:1.2.3.4.5.6.7.8.9.0.1.e164.arpa" → "sip:us-server@domain.com"

# EU number
"enum:4.4.1.2.3.4.5.6.7.8.4.e164.arpa" → "sip:eu-server@domain.com"
```

### Time-Based Routing

Use external script to update NVS based on time:

```bash
# Business hours: office phone
# After hours: mobile phone
```

## Support

### Resources

- Emercoin Wiki: <https://emercoin.com/tech-solutions>
- ENUM RFC: <https://tools.ietf.org/html/rfc6116>
- Antisip: <https://antisip.com>

### Logs Location

- Backend: `journalctl -u enum-backend`
- Nginx: `/var/log/nginx/enum-backend-*.log`
- Emercoin: `~/.emercoin/debug.log`

## License

MIT License - Free to use and modify

## Contributing

Submit issues or pull requests for improvements.
