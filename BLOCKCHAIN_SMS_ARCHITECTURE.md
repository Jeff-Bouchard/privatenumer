# Privateness.network Blockchain SMS - Technical Architecture

## System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│              Emercoin NVS Blockchain                    │
│         (Decentralized Number Registry)                 │
│                                                          │
│  sms:+1234567890 → {                                   │
│    "owner": "EMC_address",                             │
│    "pubkey": "cryptographic_public_key",               │
│    "price_per_sms": "0.001 EMC",                       │
│    "rental_rate": "0.01 EMC/day",                      │
│    "status": "available|rented",                       │
│    "reputation": 985,                                  │
│    "gateway_url": "https://gateway.ness.cx",   │
│    "last_seen": 1699564800,                            │
│    "features": ["non-voip", "usa", "instant"]         │
│  }                                                      │
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

**Purpose:** Decentralized database of available phone numbers

**Schema:**

```json
{
  "namespace": "sms:",
  "key": "+1234567890",
  "value": {
    "owner": "EMC_blockchain_address",
    "pubkey": "ED25519_public_key",
    "price_per_sms": "0.001",
    "rental_daily": "0.01",
    "rental_weekly": "0.05",
    "rental_monthly": "0.15",
    "status": "available",
    "rented_to": null,
    "rental_expires": null,
    "reputation": 985,
    "total_sms": 1250,
    "successful_sms": 1230,
    "failed_sms": 20,
    "avg_delivery_time": 2.3,
    "gateway_url": "https://gateway.example.com",
    "features": ["non-voip", "usa", "instant", "telegram-forward"],
    "last_seen": 1699564800,
    "created": 1690000000
  }
}
```

**Operations:**

```bash
# Register new number
emercoin-cli name_new "sms:+1234567890" '{"owner":"EMCaddr","pubkey":"key",...}' 365

# Update availability
emercoin-cli name_update "sms:+1234567890" '{"status":"rented","rented_to":"renter_key"}' 365

# Query available numbers
emercoin-cli name_filter "sms:" 1000 | jq '.[] | select(.value.status=="available")'

# Check number reputation
emercoin-cli name_show "sms:+1234567890" | jq '.value.reputation'
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
        
    def register_number(self, phone_number, price_per_sms, rental_rates):
        """Register number on Emercoin blockchain"""
        nv_record = {
            "owner": self.emc_address,
            "pubkey": self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex(),
            "price_per_sms": price_per_sms,
            "rental_daily": rental_rates['daily'],
            "rental_weekly": rental_rates['weekly'],
            "rental_monthly": rental_rates['monthly'],
            "status": "available",
            "gateway_url": f"https://{self.get_public_ip()}:8443",
            "features": ["non-voip", "instant"]
        }
        
        # Register via emercoin-cli
        cmd = f'emercoin-cli name_new "sms:{phone_number}" \'{json.dumps(nv_record)}\' 365'
        os.system(cmd)
        
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
- `capabilities` is a bitfield (e.g., non-voip=1, instant=2, region-us=4, voice-fwd=8).
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

## 🚀 Non-Technical Quickstart (Linux/Windows, 5 steps)

Windows users: open Git Bash and run the same Linux/macOS commands below as-is.

1. Install Python tooling with uv (recommended)

- Linux/macOS:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
exec "$SHELL" -l
uv venv
uv pip install cryptography
uv pip install git+https://github.com/ness-network/pyuheprng.git
```

- Windows (PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv venv
uv pip install cryptography
uv pip install git+https://github.com/ness-network/pyuheprng.git
```

1. Generate your identity with PrivatenessTools

- Follow PrivatenessTools: `./keygen user <username> 5`
- Export WORM: `./key worm ~/.privateness-keys/<username>.key.json`
- Publish on-chain (Emercoin):

```bash
emercoin-cli walletpassphrase "your-pass" 300
emercoin-cli name_new "worm:user:ness:<username>" '<WORM_XML_ESCAPED>' 365
```

1. Create a blind listing (privacy-first)

- Build your signed off‑chain record (JSON) with your gateway URLs and pricing.
- Compute its SHA‑256; put only this minimal JSON on-chain:

```json
{"worm_ref":"worm:user:ness:<username>","commitment":"<sha256hex>","capabilities":7,"rev":1}
```

```bash
emercoin-cli name_new "ness:sms:listing:<opaque_id>" '<MINIMAL_JSON>' 365
```

1. Send and receive securely (no coding)

- Encrypt and sign (provider side):

```bash
python tools/ptool_encrypt.py --peer-pub-b64 <renter_X25519_pub_b64url> --in sms.txt --out sms.enc
python tools/ptool_sign.py    --priv-b64     <provider_Ed25519_priv_b64url> --in sms.enc --out sms.sig
```

- Optional RANDPAY (defaults: 1 EMC, risk 1/6, 6h):

```bash
# provider
emercoin-cli randpay_mkchap 1 6 21600
# renter
emercoin-cli randpay_mktx   "<chap>" 21600 0
# provider
emercoin-cli randpay_accept "<txhex>" 2
```

- Verify and decrypt (renter side):

```bash
python tools/ptool_verify.py  --pub-b64  <provider_Ed25519_verify_b64url> --in sms.enc --sig sms.sig
python tools/ptool_decrypt.py --priv-b64 <renter_X25519_priv_b64url>      --in sms.enc --out sms.txt
```

1. Use the gateway (clearnet or EmerDNS)

- HTTPS: `https://gateway.ness.cx`
- WSS:   `wss://gateway.ness.cx/ws`
- Mirror: `https://gateway.private.ness` and `wss://gateway.private.ness/ws`

Docker (coming next): we will provide an official Dockerfile and Compose recipe to run the tools and gateway client in containers. Keep using uv-based installs for now; the containerized flow will mirror these steps.

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
  "phone_number": "+1234567890",
  "pricing": {
    "per_sms": "0.001",
    "daily": "0.01",
    "weekly": "0.05",
    "monthly": "0.15"
  },
  "features": ["non-voip", "instant", "telegram-forward"],
  "modem_port": "/dev/ttyUSB0"
}
```

#### Step 3: Register on Blockchain

```bash
# Register your number
python3 provider.py register

# Start gateway
python3 provider.py start
```

### For Renters

#### Option 1: Web Dashboard

1. Visit `https://ness.cx/dashboard`
2. Connect wallet (Emercoin address)
3. Browse available numbers
4. Rent number (payment via EMC)
5. Receive SMS in dashboard

#### Option 2: API Integration

```bash
# Get API key
curl -X POST https://gateway.ness.cx/auth \
  -H "Content-Type: application/json" \
  -d '{"emc_address":"YOUR_ADDRESS","signature":"SIGNED_CHALLENGE"}'

# Browse available numbers
curl https://gateway.ness.cx/numbers/available \
  -H "Authorization: Bearer YOUR_API_KEY"

# Rent a number
curl -X POST https://gateway.ness.cx/rent \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"number":"+1234567890","duration":"weekly"}'

# Retrieve SMS
curl https://gateway.ness.cx/sms \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---
