# Privateness.network ENUM Backend

## The Decentralized VoIP Revolution

### Antisip + Emercoin NVS: Privateness.network's Secret Weapon

This is how Privateness.network achieves **truly decentralized VoIP** - no DNS servers, no ENUM registrars, no centralized infrastructure. Just blockchain-verified phone number to SIP URI mapping using Emercoin's battle-tested Name-Value Storage.

**What makes this different:**

- ❌ **No DNS servers** - Emercoin NVS replaces ENUM DNS entirely
- **No registrars** - Direct blockchain registration, ~$0.10/year per number
- **No ICANN** - Decentralized namespace, censorship-resistant
- **Gibson's Ultra-High Entropy PRNG** - Military-grade randomness via `pyuheprng`
- **Emercoin RC4OK** - Dual-layer entropy for `random.trust_cpu=off` deployments
- **Blockchain-verified** - Cryptographic proof of number ownership
- **Global replication** - Thousands of Emercoin nodes worldwide

```text
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Antisip   │──HTTP──→│ ENUM Backend │──RPC───→│  Emercoin   │
│   Android   │         │    Flask     │         │  NVS Chain  │
└─────────────┘         └──────────────┘         └─────────────┘
```

## Prerequisites

1. Raspberry Pi with Raspberry Pi OS (or any Linux system)
2. Emercoin Core Node (`emercoind`) installed and synchronized
3. Python 3.7+
4. `emercoin-cli` accessible in PATH or at `/usr/local/bin/emercoin-cli`
5. Gibson's Ultra-High Entropy PRNG (`pyuheprng`) - installed automatically via requirements.txt

## Quick Installation

```bash
cd enum-server
sudo ./setup.sh
```

The script will:

- Verify Emercoin installation and connectivity
- Install Python dependencies (Flask, flask-cors)
- Create systemd service (`enum-backend.service`)
- Configure firewall for port 8080
- Start the ENUM backend

## Manual Installation

```bash
cd enum-server
pip3 install -r requirements.txt
python3 enum_backend.py --host 0.0.0.0 --port 8080
```

## Configuration

### Antisip Android App

Configure Antisip to use your ENUM backend:

- **ENUM Server URL**: `http://your-server-ip:8080/enum/lookup?number=`
- Antisip will query this endpoint before placing calls

### Register ENUM Records in Emercoin NVS

```bash
# Format: +1234567890 -> enum:0.9.8.7.6.5.4.3.2.1.e164.arpa
emercoin-cli name_new \
  "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  '"!^.*$!sip:user@domain.com!"' \
  365
```

**Record Format:**

- **Key**: `enum:<reversed-digits>.e164.arpa`
- **Value**: NAPTR record `"!^.*$!sip:uri!"`
- **TTL**: Days (365 = 1 year)

## API Endpoints

### Lookup ENUM Record

```bash
GET /enum/lookup?number=+1234567890
```

Response:

```json
{
  "status": "success",
  "phone_number": "+1234567890",
  "sip_uri": "sip:user@domain.com",
  "naptr_records": [
    {
      "order": 100,
      "preference": 10,
      "service": "E2U+sip",
      "replacement": "sip:user@domain.com"
    }
  ],
  "enum_domain": "0.9.8.7.6.5.4.3.2.1.e164.arpa",
  "expires_in": 12345,
  "owner_address": "EAddr..."
}
```

### Health Check

```bash
GET /health
```

### List All ENUM Records

```bash
GET /enum/list
```

## Documentation

- **[enum-server/README.md](enum-server/README.md)** - Complete API reference and deployment guide
- **[enum-server/QUICKSTART.md](enum-server/QUICKSTART.md)** - Quick setup commands
- **[enum-server/DEPLOYMENT.md](enum-server/DEPLOYMENT.md)** - Production deployment on Raspberry Pi
- **[enum-server/SECURITY_HARDENING.md](enum-server/SECURITY_HARDENING.md)** - ⚠️ Advanced security hardening (kernel RNG, system hardening)
- **[enum-server/SIM_GATEWAY.md](enum-server/SIM_GATEWAY.md)** - 📱 Optional: 3G/4G/5G modem integration for SMS/cellular fallback
- **[enum-server/SMS_SETUP.md](enum-server/SMS_SETUP.md)** - Optional SMS gateway for 2FA verification

## Troubleshooting

Check backend logs:

```bash
sudo journalctl -u enum-backend -f
```

Check Emercoin sync status:

```bash
emercoin-cli getinfo
```

Test Emercoin NVS connectivity:

```bash
emercoin-cli name_filter "enum:" 10
```
