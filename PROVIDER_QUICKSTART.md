# Provider Quickstart — Offering SMS/Voice Service

**Role:** You have real SIM cards and want to earn EMC by providing SMS/voice services.

**Platform:** Linux/macOS/Windows (Git Bash)

**Time:** ~30 minutes setup, then automated

---

## Prerequisites (one-time)

### 1. Install Emercoin Core

```bash
# Download from https://emercoin.com/downloads
# Sync blockchain (may take hours)
emercoin-cli getinfo  # verify it's running
```

### 2. Clone repositories

```bash
git clone https://github.com/ness-network/privatenesstools
git clone https://github.com/ness-network/privatenumer
cd privatenumer
```

### 3. Install Python tooling

```bash
# Linux/macOS/Windows Git Bash:
curl -Ls https://astral.sh/uv/install.sh | sh
exec "$SHELL" -l
uv venv
uv pip install cryptography
uv pip install git+https://github.com/ness-network/pyuheprng.git
```

### 4. Hardware setup

**You need:**

- Real SIM card(s) with active service
- USB modem (e.g., Huawei E3372) OR
- Android phone with USB tethering OR
- GSM gateway (multi-SIM for scale)

**Install Gammu:**

```bash
# Linux
sudo apt install gammu python3-gammu

# macOS
brew install gammu

# Windows (Git Bash)
# Download from https://wammu.eu/gammu/
```

---

## Step 1: Generate Identity

```bash
cd ../privatenesstools
./keygen user provider123 5
./key worm ~/.privateness-keys/provider123.key.json
```

**Output:**

- `~/.privateness-keys/provider123.key.json` (your keyfile — keep safe!)
- WORM XML (displayed in terminal)

---

## Step 2: Publish WORM on-chain

```bash
# Get WORM XML from previous step
WORM_XML=$(./key worm ~/.privateness-keys/provider123.key.json)

# Publish to Emercoin NVS
emercoin-cli walletpassphrase "your-wallet-password" 300
emercoin-cli name_new "worm:user:ness:provider123" "$WORM_XML" 365
```

**Cost:** ~0.01 EMC (one-time per year)

**Verify:**

```bash
emercoin-cli name_show "worm:user:ness:provider123"
```

---

## Step 3: Create Blind Listing

### Choose service tier

- **SMS-only:** `capabilities: 11` (~0.01 EMC/day rental)
- **SMS+Voice/Video:** `capabilities: 123` (~0.05 EMC/day rental)

See [SERVICE_TIERS.md](SERVICE_TIERS.md) for comparison.

### Build off-chain record

```bash
cd ../privatenumer

# Create off-chain listing (example for SMS-only)
cat > listing_offchain.json <<'EOF'
{
  "provider_id": "provider123",
  "service_tiers": {
    "sms_only": {
      "enabled": true,
      "pricing": {
        "per_sms": "0.001",
        "rental_daily": "0.01",
        "rental_weekly": "0.05",
        "rental_monthly": "0.15"
      }
    }
  },
  "gateway_endpoints": {
    "https": "https://gateway.ness.cx",
    "wss": "wss://gateway.ness.cx/ws"
  },
  "features": ["non-voip", "instant"],
  "timestamp": $(date +%s)
}
EOF

# Sign it
python tools/ptool_sign.py \
  --priv-keyfile ~/.privateness-keys/provider123.key.json \
  --priv-field ed25519.private \
  --in listing_offchain.json \
  --out listing_offchain.sig

# Compute commitment
COMMITMENT=$(cat listing_offchain.json | jq -c -S . | sha256sum | awk '{print $1}')

# Generate opaque ID
OPAQUE_ID=$(uuidgen | tr -d '-' | head -c 16)

# Publish minimal on-chain JSON
MINIMAL_JSON=$(cat <<EOF
{"worm_ref":"worm:user:ness:provider123","commitment":"$COMMITMENT","capabilities":11,"rev":1}
EOF
)

emercoin-cli name_new "ness:sms:listing:$OPAQUE_ID" "$MINIMAL_JSON" 365

echo "✅ Listing published: ness:sms:listing:$OPAQUE_ID"
echo "📄 Off-chain record: listing_offchain.json"
echo "✍️  Signature: listing_offchain.sig"
```

**Cost:** ~0.01 EMC (one-time per year)

**Save these:**

- `$OPAQUE_ID` (your listing ID)
- `listing_offchain.json` (publish to IPFS or serve via gateway)
- `listing_offchain.sig` (proof of authenticity)

---

## Step 4: Configure Gateway Software

### Option A: Simple Python Gateway (recommended for testing)

```bash
cd enum-server

# Configure Gammu
cat > ~/.gammurc <<EOF
[gammu]
device = /dev/ttyUSB0
connection = at
EOF

# Test SIM connection
gammu identify

# Start gateway
python enum_backend.py
```

### Option B: Production Gateway (Asterisk + Gammu)

See [SIM_GATEWAY.md](enum-server/SIM_GATEWAY.md) for full setup.

---

## Step 5: Receive and Forward SMS

**When SMS arrives at your SIM:**

```bash
# Encrypt for renter (using their keyfile)
python tools/ptool_encrypt.py \
  --peer-pub-keyfile ~/.privateness-keys/renter456.key.json \
  --peer-pub-field x25519.public \
  --in sms_received.txt \
  --out sms.enc

# Sign envelope
python tools/ptool_sign.py \
  --priv-keyfile ~/.privateness-keys/provider123.key.json \
  --priv-field ed25519.private \
  --in sms.enc \
  --out sms.sig

# Forward to gateway (via Skywire)
curl -X POST https://gateway.ness.cx/forward \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "listing_id": "$OPAQUE_ID",
  "envelope": "$(cat sms.enc)",
  "signature": "$(cat sms.sig)"
}
EOF
```

**This will be automated by gateway software.**

---

## Step 6: Handle RANDPAY Micropayments

**When renter requests service:**

```bash
# Create challenge (1 EMC, 1/6 probability, 6h timeout)
CHAP=$(emercoin-cli randpay_mkchap 1 6 21600 | jq -r .reply)
echo "Send this to renter: $CHAP"

# After renter sends txhex, verify and accept
RESULT=$(emercoin-cli randpay_accept "<txhex_from_renter>" 2)
echo $RESULT | jq .

# Check if won
WON=$(echo $RESULT | jq -r .won)
if [ "$WON" = "true" ]; then
  echo "✅ Payment received: 1 EMC"
else
  echo "⚠️  No payment (probability: 1/6)"
fi
```

**Expected revenue:** ~1/6 EMC per attempt = ~0.167 EMC per message

---

## Ongoing Operations

### Monitor rentals

```bash
# Check your listing
emercoin-cli name_show "ness:sms:listing:$OPAQUE_ID"

# View rental history (via gateway API)
curl https://gateway.ness.cx/provider/rentals \
  -H "Authorization: Bearer <your_token>"
```

### Renew NVS records

```bash
# Renew WORM (yearly)
emercoin-cli name_update "worm:user:ness:provider123" "$WORM_XML" 365

# Renew listing (yearly)
emercoin-cli name_update "ness:sms:listing:$OPAQUE_ID" "$MINIMAL_JSON" 365
```

### Update pricing

```bash
# Edit listing_offchain.json with new prices
nano listing_offchain.json

# Re-sign
python tools/ptool_sign.py \
  --priv-keyfile ~/.privateness-keys/provider123.key.json \
  --priv-field ed25519.private \
  --in listing_offchain.json \
  --out listing_offchain.sig

# Compute new commitment
NEW_COMMITMENT=$(cat listing_offchain.json | jq -c -S . | sha256sum | awk '{print $1}')

# Update on-chain (increment rev)
UPDATED_JSON=$(cat <<EOF
{"worm_ref":"worm:user:ness:provider123","commitment":"$NEW_COMMITMENT","capabilities":11,"rev":2}
EOF
)

emercoin-cli name_update "ness:sms:listing:$OPAQUE_ID" "$UPDATED_JSON" 365
```

---

## Troubleshooting

### SIM not detected

```bash
# List USB devices
lsusb

# Check modem
ls -l /dev/ttyUSB*

# Test Gammu
gammu identify
```

### SMS not forwarding

```bash
# Check gateway logs
tail -f gateway.log

# Test encryption manually
echo "test" > test.txt
python tools/ptool_encrypt.py \
  --peer-pub-keyfile ~/.privateness-keys/renter456.key.json \
  --peer-pub-field x25519.public \
  --in test.txt \
  --out test.enc
```

### RANDPAY not working

```bash
# Check Emercoin wallet balance
emercoin-cli getbalance

# Verify wallet is unlocked
emercoin-cli walletpassphrase "your-pass" 300

# Test RANDPAY
emercoin-cli randpay_mkchap 1 6 21600
```

---

## Economics

### Break-even analysis (SMS-only tier)

**Costs:**

- SIM card: ~$10-20/month
- Electricity: ~$5/month
- Internet: ~$20/month (if dedicated)
- **Total:** ~$35-45/month

**Revenue (at 0.01 EMC/day rental):**

- 1 renter: 0.3 EMC/month (~$3-6 at $10-20/EMC)
- 10 renters: 3 EMC/month (~$30-60)
- 30 renters: 9 EMC/month (~$90-180)

**Break-even:** ~10-15 renters per SIM

**Plus RANDPAY per-message fees:** ~0.001 EMC/SMS

---

## Security Best Practices

1. **Keep keyfile safe:** `~/.privateness-keys/provider123.key.json`
2. **Encrypt backups:** Use PrivatenessTools `key pack` command
3. **Use burner identity:** Don't link to personal info
4. **Physical security:** SIM cards can be seized
5. **Jurisdictional arbitrage:** Operate in privacy-friendly countries
6. **Rotate SIMs:** Replace periodically to avoid tracking

---

## Next Steps

- **Scale up:** Add more SIM cards (see [SIM_GATEWAY.md](enum-server/SIM_GATEWAY.md))
- **Automate:** Set up cron jobs for renewal, monitoring
- **Optimize:** Tune pricing based on demand
- **Expand:** Offer SMS+Voice/Video tier for higher revenue

---

## Support

- **Docs:** [BLOCKCHAIN_SMS_ARCHITECTURE.md](BLOCKCHAIN_SMS_ARCHITECTURE.md)
- **Gateway:** <https://gateway.ness.cx>
- **Community:** (TBD)
