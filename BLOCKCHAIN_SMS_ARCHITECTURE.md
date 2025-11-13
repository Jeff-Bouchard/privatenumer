# Privateness.network Blockchain SMS - Technical Architecture

## System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│              Emercoin NVS Blockchain                    │
│         (Privacy-First Blind Listings)                  │
│                                                          │
│  ness:sms:listing:<opaque_id> → {                      │
│    "worm_ref": "worm:user:ness:provider123",          │
│    "commitment": "<sha256_of_offchain_record>",       │
│    "capabilities": 7,                                  │
│    "rev": 1                                            │
│  }                                                      │
│                                                          │
│  Off-chain signed record contains:                      │
│  - Gateway endpoints, pricing, features                 │
│  - Verified against commitment hash                     │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│          Privateness.network Gateway Layer              │
│           (Decentralized Relay Network)                 │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Gateway Node │  │ Gateway Node │  │ Gateway Node │ │
│  │   (USA)      │  │   (Europe)   │  │   (Asia)     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│         Number Providers (Phone Owners)                 │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Android App  │  │ USB Modem    │  │ GSM Gateway  │ │
│  │ + Real SIM   │  │ + Real SIM   │  │ + Real SIM   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  Earn EMC by providing SMS receiving services           │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│               End Users (Renters)                       │
│                                                          │
│  - Web Dashboard                                        │
│  - REST API                                             │
│  - Telegram Bot                                         │
│  - Mobile Apps                                          │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Blockchain Registry (Emercoin NVS)

**Purpose:** Privacy-first blind listing registry with minimal on-chain footprint

**On-chain schema (ness:sms:listing:<opaque_id>):**

```json
{
  "namespace": "ness:sms:listing:",
  "key": "<opaque_id>",
  "value": {
    "worm_ref": "worm:user:ness:provider123",
    "commitment": "<sha256hex_of_offchain_record>",
    "capabilities": 7,
    "rev": 1
  }
}
```

**Off-chain signed record (verified against commitment):**

```json
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
    },
    "sms_voice_video": {
      "enabled": true,
      "pricing": {
        "per_sms": "0.001",
        "per_minute_voice": "0.01",
        "per_minute_video": "0.02",
        "rental_daily": "0.05",
        "rental_weekly": "0.25",
        "rental_monthly": "0.80"
      },
      "sip_endpoint": "sip:gateway@gateway.ness.cx",
      "enum_support": true
    }
  },
  "gateway_endpoints": {
    "https": "https://gateway.ness.cx",
    "wss": "wss://gateway.ness.cx/ws"
  },
  "features": ["non-voip", "usa", "instant"],
  "reputation": 985,
  "pubkey_encrypt": "<X25519_base64url>",
  "pubkey_verify": "<Ed25519_base64url>",
  "timestamp": 1699564800,
  "signature": "<Ed25519_detached_sig>"
}
```

**Service Tiers:**

- **SMS-only:** Receive SMS for verification, 2FA, notifications. No voice/video. Lower cost.
- **SMS+Voice/Video:** Full communication suite. Receive calls via SIP (Antisip, Linphone). Higher cost.

**Operations:**

```bash
# Register new blind listing (provider)
OPAQUE_ID=$(uuidgen | tr -d '-' | head -c 16)
MINIMAL_JSON='{"worm_ref":"worm:user:ness:provider123","commitment":"<sha256hex>","capabilities":7,"rev":1}'
emercoin-cli name_new "ness:sms:listing:$OPAQUE_ID" "$MINIMAL_JSON" 365

# Query all blind listings
emercoin-cli name_filter "ness:sms:listing:" 1000

# Show specific listing
emercoin-cli name_show "ness:sms:listing:<opaque_id>"

# Verify off-chain record against commitment
echo -n '<offchain_json>' | sha256sum  # must match commitment field
```

### 2. Provider Gateway Software

**Three Options:**

#### Option A: Android App (Easiest)

```kotlin
// PrivatenessGateway Android App
class SMSReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            messages.forEach { sms ->
                // Forward to gateway API
                forwardSMS(
                    from = sms.originatingAddress,
                    body = sms.messageBody,
                    timestamp = sms.timestampMillis
                )
            }
        }
    }
    
    fun forwardSMS(from: String, body: String, timestamp: Long) {
        // Encrypt with renter's public key
        val encrypted = encrypt(body, renterPubKey)
        
        // Send to gateway network
        api.forwardSMS(encrypted, signature, providerKey)
        
        // Update blockchain reputation
        updateReputation(providerKey, true)
    }
}
```

#### Option B: Raspberry Pi + USB Modem (What We Documented)

```python
#!/usr/bin/env python3
"""
Privateness.network SMS Gateway Provider
Integrates with existing SIM_GATEWAY.md architecture
"""

import gammu
import requests
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

class PrivatenessProvider:
    def __init__(self, emc_address, private_key):
        self.emc_address = emc_address
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
        self.public_key = self.private_key.public_key()
        
        # Initialize Gammu (from SIM_GATEWAY.md)
        self.state_machine = gammu.StateMachine()
        self.state_machine.ReadConfig()
        self.state_machine.Init()
        
    def register_blind_listing(self, provider_id, price_per_sms, rental_rates):
        """Register privacy-first blind listing on Emercoin blockchain"""
        import hashlib
        import uuid
        
        # Build off-chain signed record
        offchain_record = {
            "provider_id": provider_id,
            "gateway_endpoints": {
                "https": "https://gateway.ness.cx",
                "wss": "wss://gateway.ness.cx/ws"
            },
            "pricing": {
                "per_sms": price_per_sms,
                "rental_daily": rental_rates['daily'],
                "rental_weekly": rental_rates['weekly'],
                "rental_monthly": rental_rates['monthly']
            },
            "features": ["non-voip", "instant"],
            "pubkey_encrypt": self.x25519_pubkey_b64url,
            "pubkey_verify": self.ed25519_pubkey_b64url,
            "timestamp": int(time.time())
        }
        
        # Sign off-chain record
        canonical = json.dumps(offchain_record, separators=(',', ':'), sort_keys=True)
        signature = self.private_key.sign(canonical.encode('utf-8'))
        offchain_record['signature'] = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        # Compute commitment
        commitment = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        
        # Generate opaque ID
        opaque_id = uuid.uuid4().hex[:16]
        
        # Minimal on-chain JSON
        minimal_json = {
            "worm_ref": f"worm:user:ness:{provider_id}",
            "commitment": commitment,
            "capabilities": 7,  # bitfield: non-voip=1, instant=2, region-us=4
            "rev": 1
        }
        
        # Register via emercoin-cli
        cmd = f'emercoin-cli name_new "ness:sms:listing:{opaque_id}" \'{json.dumps(minimal_json)}\' 365'
        os.system(cmd)
        
        # Store off-chain record locally or publish to IPFS/gateway
        with open(f'listings/{opaque_id}.json', 'w') as f:
            json.dump(offchain_record, f, indent=2)
        
    def listen_for_sms(self):
        """Monitor for incoming SMS"""
        while True:
            # Check for new SMS
            sms_list = self.state_machine.GetSMS(Folder=0, Location=0)
            
            for sms in sms_list:
                self.handle_incoming_sms(
                    from_number=sms['Number'],
                    message=sms['Text'],
                    timestamp=sms['DateTime']
                )
                
                # Delete processed SMS
                self.state_machine.DeleteSMS(Folder=0, Location=sms['Location'])
            
            time.sleep(1)
    
    def handle_incoming_sms(self, from_number, message, timestamp):
        """Forward SMS to renter"""
        # Get current rental info from blockchain
        rental_info = self.get_rental_info()
        
        if rental_info and rental_info['rented_to']:
            # Encrypt message with renter's public key
            encrypted = self.encrypt_for_renter(message, rental_info['rented_to'])
            
            # Sign with provider's private key
            signature = self.private_key.sign(encrypted)
            
            # Forward through gateway network
            response = requests.post('https://gateway.ness.cx/forward', json={
                'provider': self.emc_address,
                'encrypted_message': encrypted.hex(),
                'signature': signature.hex(),
                'from': from_number,
                'timestamp': timestamp.isoformat()
            })
            
            if response.status_code == 200:
                # Payment received, update reputation
                self.update_reputation(success=True)
            else:
                self.update_reputation(success=False)
```

#### Option C: Dedicated GSM Gateway (Enterprise)

```python
"""
Multi-SIM GSM Gateway for Privateness.network
Handles 8-32 SIM cards simultaneously
"""

import asyncio
from typing import List

class MultiSIMGateway:
    def __init__(self, sim_slots: List[str]):
        self.sim_slots = sim_slots  # ['/dev/ttyUSB0', '/dev/ttyUSB1', ...]
        self.providers = {}
        
    async def initialize_all_sims(self):
        """Initialize all SIM slots in parallel"""
        tasks = [self.initialize_sim(slot) for slot in self.sim_slots]
        await asyncio.gather(*tasks)
        
    async def initialize_sim(self, slot):
        """Initialize single SIM gateway"""
        provider = PrivatenessProvider(
            emc_address=f"EMC_{slot}",
            private_key=get_key_for_slot(slot)
        )
        provider.listen_for_sms()
        self.providers[slot] = provider
```

### 3. Gateway Network Layer

**Purpose:** Relay encrypted SMS between providers and renters

**Features:**

- Load balancing across multiple gateway nodes
- Geographic distribution (USA, Europe, Asia)
- DDoS protection
- Rate limiting
- WebSocket support for real-time delivery

**API Endpoints:**

```python
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

@app.route('/forward', methods=['POST'])
def forward_sms():
    """Provider → Gateway → Renter"""
    data = request.json
    
    # Verify provider signature
    if not verify_signature(data['provider'], data['signature'], data['encrypted_message']):
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Verify payment in escrow
    if not check_escrow_balance(data['provider']):
        return jsonify({'error': 'Insufficient escrow'}), 402
    
    # Forward to renter
    renter_info = get_renter_from_blockchain(data['provider'])
    
    # Send via WebSocket if online
    if renter_info['online']:
        send_websocket(renter_info['connection_id'], data)
    else:
        # Queue for later retrieval
        queue_message(renter_info['pubkey'], data)
    
    # Deduct payment from escrow
    process_payment(renter_info['pubkey'], data['provider'], amount=get_price_per_sms(data['provider']))
    
    return jsonify({'status': 'delivered'}), 200

@app.route('/retrieve', methods=['GET'])
def retrieve_sms():
    """Renter retrieves queued SMS"""
    auth_token = request.headers.get('Authorization')
    renter_pubkey = verify_jwt(auth_token)
    
    # Get queued messages
    messages = get_queued_messages(renter_pubkey)
    
    return jsonify({'messages': messages}), 200
```

### 4. Renter Interface

**Web Dashboard:**

```javascript
// React Dashboard for Renters
import React, { useState, useEffect } from 'react';

function SMSDashboard() {
  const [availableNumbers, setAvailableNumbers] = useState([]);
  const [rentedNumbers, setRentedNumbers] = useState([]);
  const [messages, setMessages] = useState([]);
  
  // Browse marketplace
  useEffect(() => {
    fetch('https://gateway.ness.cx/numbers/available')
      .then(res => res.json())
      .then(data => setAvailableNumbers(data));
  }, []);
  
  // Rent number
  const rentNumber = async (number, duration) => {
    const response = await fetch('https://gateway.ness.cx/rent', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        number: number,
        duration: duration,
        payment: calculatePayment(number, duration)
      })
    });
    
    if (response.ok) {
      alert(`Successfully rented ${number}`);
      fetchRentedNumbers();
    }
  };
  
  // Real-time SMS via WebSocket
  useEffect(() => {
    const ws = new WebSocket('wss://gateway.ness.cx/ws');
    
    ws.onmessage = (event) => {
      const sms = JSON.parse(event.data);
      // Decrypt with user's private key
      const decrypted = decryptMessage(sms.encrypted_message, userPrivateKey);
      setMessages(prev => [...prev, decrypted]);
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <div>
      <h1>Available Numbers</h1>
      {availableNumbers.map(num => (
        <NumberCard 
          key={num.number}
          number={num.number}
          price={num.price_per_sms}
          reputation={num.reputation}
          onRent={() => rentNumber(num.number, 'weekly')}
        />
      ))}
      
      <h1>Received SMS</h1>
      {messages.map(msg => (
        <SMSCard 
          key={msg.timestamp}
          from={msg.from}
          message={msg.message}
          timestamp={msg.timestamp}
        />
      ))}
    </div>
  );
}
```

## 🔐 Identity and WORM Records (PrivatenessTools)

Use NessNodeTester to generate user identities and publish them on-chain as WORM records.

1. Install tools

```bash
git clone https://github.com/NESS-Network/NessNodeTester
pip install requests pynacl pycryptodome validators lxml
```

1. Generate a provider user

```bash
python codegen.py -ug <provider_username> 10 "1,blowfish,16;1,aes,8" "SMSProvider,USA"
python codegen.py -usw <provider_username>   # shows WORM to publish in NVS
```

1. Publish user WORM in Emercoin NVS

```bash
emercoin-cli walletpassphrase "your-pass" 300  # if needed
emercoin-cli name_new "worm:user:ness:<provider_username>" '<WORM_XML_ESCAPED>' 365
```

The user WORM contains the canonical `public` (encryption) and `verify` (signature verification) keys for application-layer operations.

## 🕶️ SMS Blind Listing Record (ness:sms:listing:<opaque_id>)

Publish a privacy-preserving listing keyed by `ness:sms:listing:<opaque_id>` that references the provider’s user WORM and anchors a commitment to the off-chain record.

On-chain value (minimal JSON):

```json
{
  "worm_ref": "worm:user:ness:provider123",
  "commitment": "<sha256hex_of_offchain_record>",
  "capabilities": 7,
  "rev": 1
}
```

Notes:

- Do not publish E.164, keys, endpoints, or pricing in clear on-chain.
- `capabilities` is a bitfield:
  - `1` (0x01): non-VOIP (real SIM)
  - `2` (0x02): instant delivery
  - `4` (0x04): region-us
  - `8` (0x08): SMS-only tier available
  - `16` (0x10): voice calls supported
  - `32` (0x20): video calls supported
  - `64` (0x40): ENUM/SIP routing
  - Example: `capabilities: 27` = non-voip + instant + region-us + SMS-only (1+2+4+8+16)
- The canonical off-chain record (signed by provider) contains operational details and is verified against `commitment`.

Publish:

```bash
emercoin-cli name_new "ness:sms:listing:<opaque_id>" '<MINIMAL_JSON>' 365
emercoin-cli name_show "ness:sms:listing:<opaque_id>"
```

## 💼 Escrow Anchoring (ness:escrow:<opaque_id>)

Anchor the multisig 2-of-3 escrow descriptor or a hash commitment to an off-chain policy document.

Examples:

```json
{
  "descriptor": "wsh(multi(2,PK_R,PK_P,PK_A))",
  "policy": {"release": "2of3", "fees_bps": 50}
}
```

or

```json
{
  "escrow_commitment": "<sha256hex_of_offchain_escrow_policy>"
}
```

Publish:

```bash
emercoin-cli name_new "ness:escrow:<opaque_id>" '<ESCROW_JSON>' 365
```

## 🧾 Proofs Anchoring (ness:proofs:sms:`<YYYYMMDD>`)

Periodically anchor Merkle roots of signed delivery receipts for auditability.

On-chain value:

```json
{
  "merkle_root": "<hex>",
  "count": 1234,
  "period": "2025-11-13T00:00:00Z/24h"
}
```

## 🌐 Endpoints

- 🌎 HTTPS: `https://gateway.ness.cx`
- 🔌 WebSocket: `wss://gateway.ness.cx/ws`
- 🧭 EmerDNS mirror: `https://gateway.private.ness` and `wss://gateway.private.ness/ws`
- 📞 SIP (voice/video): `sip:gateway@gateway.ness.cx` (via Skywire)

---

## 📞 Voice/Video Call Flow (SMS+Voice/Video Tier)

### Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  Caller (PSTN/Mobile)                                   │
│  Dials: +1234567890                                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Provider's Real SIM Card                               │
│  Receives incoming call                                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Provider Gateway (Gammu/Asterisk)                      │
│  - Looks up rental mapping (local encrypted DB)         │
│  - Finds renter's SIP endpoint                          │
│  - Encrypts call metadata + audio stream                │
└─────────────────────────────────────────────────────────┘
                            ↓ (via Skywire)
┌─────────────────────────────────────────────────────────┐
│  Gateway Relay (gateway.ness.cx)                        │
│  - Receives encrypted SIP INVITE                        │
│  - Routes to renter via Skywire tunnel                  │
└─────────────────────────────────────────────────────────┘
                            ↓ (via Skywire)
┌─────────────────────────────────────────────────────────┐
│  Renter's SIP Client (Antisip/Linphone)                 │
│  - Receives call via Skywire                            │
│  - Decrypts with renter's private key                   │
│  - Rings phone/computer                                 │
└─────────────────────────────────────────────────────────┘
```

### Number Assignment

**When renter selects SMS+Voice/Video tier:**

1. Provider assigns a real E.164 number from their pool (off-chain)
2. Renter receives:
   - The actual phone number (e.g., +1234567890)
   - SIP credentials for their client
   - Rental duration and pricing
3. Renter configures Antisip/Linphone with:
   - SIP server: `gateway.ness.cx` (via Skywire)
   - Username: `<renter_id>`
   - Password: `<ephemeral_credential>`
4. Renter gives out the number to contacts
5. Incoming calls/SMS route: `PSTN → Provider SIM → Gateway → Skywire → Renter`

### ENUM Integration (Optional)

Providers can publish ENUM records for advanced routing:

```bash
# ENUM record points to provider's gateway (not directly to renter)
emercoin-cli name_new "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  'NAPTR 100 10 "u" "E2U+sip" "!^.*$!sip:gateway@gateway.ness.cx!" .' 365
```

**Privacy note:** ENUM records are public but only reveal the provider's gateway endpoint, not the renter's identity or SIP credentials.

### Outbound Calls

**Renter can make outbound calls:**

1. Renter initiates call via SIP client
2. Call routes via Skywire to gateway
3. Gateway forwards to provider's SIM
4. Provider's SIM makes PSTN call
5. Caller ID shows the rented number (+1234567890)

**Privacy:** Provider sees call metadata (destination, duration) but audio is encrypted end-to-end if both parties use SIP/SRTP.

### Video Calls

**For video-enabled tiers:**

- Uses SIP + RTP/SRTP for media
- Video codecs: H.264, VP8, VP9
- Bandwidth: ~1-2 Mbps per direction
- Routed via Skywire (provider doesn't see video content)

### Antisip Configuration

**Renter's Antisip config (auto-generated by gateway):**

```json
{
  "sip": {
    "account": {
      "username": "<renter_id>",
      "password": "<ephemeral_credential>",
      "domain": "gateway.ness.cx",
      "proxy": "sip:gateway.ness.cx:5060",
      "transport": "skywire"
    },
    "assigned_number": "+1234567890",
    "rental_expires": 1699564800
  },
  "enum": {
    "enabled": false,
    "comment": "ENUM lookup handled by provider gateway"
  }
}
```

---

## 💸 Payments and Escrow

Model: Multisig UTXO escrow (2-of-3) with roles: renter, provider, arbiter. Funds lock to a script; release requires any 2 signatures. This aligns with Emercoin’s UTXO and avoids non-existent EVM-style contracts.

---

## 🎲 RANDPAY Probabilistic Micropayments (Emercoin)

Use Emercoin’s built-in RANDPAY for scalable, stateless micropayments. It uses probabilistic wins; only winning attempts broadcast on-chain.

- ✅ Local JSON-RPC via `emercoin-cli` (no WSS involved)
- 🔐 Fits our privacy model: carried off-chain in the session; no NVS exposure

Defaults in onboarding UI:

- Amount per win: 1 EMC
- Probability: 1/6 (risk = 6)
- Risk window (timeout): 6 hours (21600 seconds)

Flow and exact commands:

- Provider (payee) creates challenge (chap):

```bash
emercoin-cli randpay_mkchap 1 6 21600
# returns: "reply" -> "risk:chap"
```

- Renter (payer) creates transaction for chap:

```bash
emercoin-cli randpay_mktx "<chap>" 21600 0
# returns: "transaction" -> hex string (txhex)
```

- Provider verifies and conditionally sends (based on win):

```bash
emercoin-cli randpay_accept "<txhex>" 2
# flags: 0=send_always 1=exact_only 2=send_or_more 3=dont_send
# returns JSON: { "txid": "...", "amount": 1.00000000, "won": true|false, "flags": 2 }
```

Notes:

- Expected spend per attempt ≈ amount / risk = 1 / 6 EMC.
- App-level budget can be enforced by counting cumulative wins per session/window.
- Rotate chap after accept or when `timeout` elapses.

---

## 🚀 Non-Technical Quickstart

**Windows users:** Open Git Bash and run Linux/macOS commands as-is.

### Step 0: Prerequisites (one-time setup)

**Install Emercoin Core:**

```bash
# Download from https://emercoin.com/downloads
# Sync blockchain (may take hours)
emercoin-cli getinfo  # verify it's running
```

**Clone repositories:**

```bash
git clone https://github.com/ness-network/privatenesstools
git clone https://github.com/ness-network/privatenumer
cd privatenumer
```

**Install Python tooling:**

```bash
# Linux/macOS/Windows Git Bash:
curl -Ls https://astral.sh/uv/install.sh | sh
exec "$SHELL" -l
uv venv
uv pip install cryptography
uv pip install git+https://github.com/ness-network/pyuheprng.git
```

---

### For Providers (offering SMS/voice service)

#### Step 1: Generate identity

```bash
cd ../privatenesstools
./keygen user provider123 5
./key worm ~/.privateness-keys/provider123.key.json
```

This creates:

- `~/.privateness-keys/provider123.key.json` (your keyfile)
- WORM XML output (copy this)

#### Step 2: Publish WORM on-chain

```bash
# Get WORM XML from previous step
WORM_XML=$(./key worm ~/.privateness-keys/provider123.key.json)

# Publish to Emercoin NVS
emercoin-cli walletpassphrase "your-wallet-password" 300
emercoin-cli name_new "worm:user:ness:provider123" "$WORM_XML" 365
```

#### Step 3: Create blind listing

**Choose service tier:**

- **SMS-only:** `capabilities: 11` (~0.01 EMC/day)
- **SMS+Voice/Video:** `capabilities: 123` (~0.05 EMC/day)

See [SERVICE_TIERS.md](SERVICE_TIERS.md) for comparison.

**Build off-chain record:**

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

echo "Listing published: ness:sms:listing:$OPAQUE_ID"
echo "Off-chain record: listing_offchain.json"
echo "Signature: listing_offchain.sig"
```

#### Step 4: Receive and forward SMS

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

**Optional: RANDPAY micropayment**

```bash
# Create challenge
CHAP=$(emercoin-cli randpay_mkchap 1 6 21600 | jq -r .reply)
echo "Send this to renter: $CHAP"

# After renter sends txhex, verify and accept
emercoin-cli randpay_accept "<txhex_from_renter>" 2
```

---

### For Renters/Users (mobile-first)

**Renters use mobile apps — no terminal commands needed.**

#### Step 1: Install apps

**Android/iOS:**

1. Install **Antisip** (SMS/voice client)
   - Download from: [antisip.app](https://antisip.app) or app stores
   - Handles: SMS reception, voice/video calls, encryption, signatures

2. Install **Privateness Wallet** (for EMC payments)
   - Download from: [wallet.ness.cx](https://wallet.ness.cx)
   - Handles: RANDPAY micropayments, escrow, EMC balance

#### Step 2: Create identity (in Antisip)

**Open Antisip → Settings → Create Identity:**

- App generates Ed25519 + X25519 keypairs
- Encrypted backup to device storage
- Optional: Export to Privateness Wallet for cross-device sync

**No CLI, no terminal, no keyfiles to manage manually.**

#### Step 3: Browse and rent a listing (in Antisip)

**Open Antisip → Browse Listings:**

1. App queries Emercoin NVS via gateway (over Skywire)
2. Filter by:
   - Service tier (SMS-only or SMS+Voice/Video)
   - Region (USA, Europe, Asia)
   - Price range
   - Provider reputation
3. Tap a listing to view details:
   - Off-chain record (auto-fetched from gateway/IPFS)
   - Commitment verification (automatic)
   - Signature verification (automatic)
   - Provider WORM lookup (automatic)
4. Tap **Rent** → Choose duration (daily/weekly/monthly)
5. Pay with Privateness Wallet:
   - RANDPAY micropayment (1 EMC, 1/6 probability)
   - Or escrow (for longer rentals)
6. Done! Listing is now active.

**For SMS+Voice/Video tier:**

- App auto-configures SIP client
- You receive a real phone number (e.g., +1234567890)
- Give this number to contacts

#### Step 4: Receive SMS/calls (automatic)

**SMS-only tier:**

- SMS arrives at provider's SIM
- Provider encrypts + signs → forwards to gateway
- Gateway routes via Skywire to your Antisip app
- App decrypts + verifies signature
- You see SMS in Antisip inbox

**SMS+Voice/Video tier:**

- Same as above, plus:
- Voice calls ring in Antisip (via SIP over Skywire)
- Video calls supported (H.264, VP8)
- Outbound calls: dial from Antisip, caller ID shows your rented number

**All encryption, signatures, and verification happen automatically in the app.**

#### Step 5: Manage rentals (in Antisip)

**Antisip → My Rentals:**

- View active listings
- Check expiration dates
- Renew before expiration (auto-payment via Privateness Wallet)
- View SMS/call history
- Export receipts (signed delivery proofs)

---

### For Advanced Users (CLI/API)

If you want to integrate programmatically or run your own client:

---

### Gateway Endpoints

- **HTTPS:** `https://gateway.ness.cx`
- **WSS:** `wss://gateway.ness.cx/ws`
- **EmerDNS mirrors:** `https://gateway.private.ness`, `wss://gateway.private.ness/ws`

### One-Click Script

For the full automated flow, use the onboarding UI:

```bash
cd onboarding/ui
python -m http.server 8000
# Open http://localhost:8000 in browser
# Click "Generate full script" button
```

---

## 📦 Deployment Guide

### 🛰️ For Providers

#### Step 1: Install Provider Software

```bash
# Clone repository
git clone https://github.com/ness-network/sms-provider.git
cd sms-provider

# Install dependencies
pip3 install -r requirements.txt

# Generate cryptographic keys
python3 generate_keys.py
```

#### Step 2: Configure Gateway

```bash
# Edit config.json
{
  "emc_address": "YOUR_EMC_ADDRESS",
  "provider_id": "provider123",
  "pricing": {
    "per_sms": "0.001",
    "daily": "0.01",
    "weekly": "0.05",
    "monthly": "0.15"
  },
  "features": ["non-voip", "instant"],
  "modem_port": "/dev/ttyUSB0",
  "gateway_endpoints": {
    "https": "https://gateway.ness.cx",
    "wss": "wss://gateway.ness.cx/ws"
  }
}
```

#### Step 3: Register Blind Listing on Blockchain

```bash
# Generate WORM and publish identity first
python3 provider.py generate-identity

# Register blind listing (privacy-first)
python3 provider.py register-listing

# Start gateway
python3 provider.py start
```

### For Renters

#### Option 1: Web Dashboard

1. Visit `https://ness.cx/dashboard`
2. Connect wallet (Emercoin address)
3. Browse available blind listings (filtered by capabilities)
4. Verify off-chain record against commitment
5. Rent listing (payment via EMC or RANDPAY)
6. Receive encrypted SMS in dashboard

#### Option 2: API Integration

```bash
# Get API key
curl -X POST https://gateway.ness.cx/auth \
  -H "Content-Type: application/json" \
  -d '{"emc_address":"YOUR_ADDRESS","signature":"SIGNED_CHALLENGE"}'

# Browse available blind listings
curl https://gateway.ness.cx/listings/available \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get off-chain record for a listing
curl https://gateway.ness.cx/listings/<opaque_id>/offchain \
  -H "Authorization: Bearer YOUR_API_KEY"

# Rent a listing
curl -X POST https://gateway.ness.cx/rent \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"listing_id":"<opaque_id>","duration":"weekly"}'

# Retrieve SMS
curl https://gateway.ness.cx/sms \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---
