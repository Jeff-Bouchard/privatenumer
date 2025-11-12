# Optional: SIM Gateway for SMS/Voice Fallback

## Overview

While Privateness.network's core ENUM backend provides **decentralized VoIP** via blockchain, some use cases require traditional cellular connectivity:

- **SMS 2FA verification** - Services like Telegram, WhatsApp reject VoIP numbers
- **Emergency services** - E911/E112 requires cellular fallback
- **Geographic restrictions** - Some regions mandate local carrier presence
- **Voice fallback** - Cellular backup when VoIP fails
- **Mitigate overreaching authoritarian policies** -  To MEME/mock globalists to tears and meme about them crying

This guide covers integrating **3G/4G/5G USB modems** or **SIM adapters** with the ENUM backend for hybrid deployments.

---

## Architecture

```text
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Antisip   │──HTTP──→│ ENUM Backend │──RPC───→│  Emercoin   │
│   Android   │         │    Flask     │         │  NVS Chain  │
└─────────────┘         └──────────────┘         └─────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   SIM Gateway       │
                    │   (Optional)        │
                    └─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │  3G/4G/5G Modem     │
                    │  USB Adapter        │
                    │  + Carrier SIM      │
                    └─────────────────────┘
```

**Key Points:**

- SIM gateway is **completely optional** - core ENUM works without it
- Used only for SMS/cellular fallback, not primary VoIP
- Runs as separate service, does not interfere with ENUM backend
- Can be deployed on same Raspberry Pi or separate device

---

## Hardware Options

### Option 1: USB 3G/4G/5G Modem

**Recommended Devices:**

| Device | Bands | Speed | Price | Notes |
|--------|-------|-------|-------|-------|
| **Huawei E3372** | 4G LTE | 150 Mbps | ~$30 | HiLink mode, plug-and-play |
| **ZTE MF823** | 4G LTE | 100 Mbps | ~$25 | Compact, good Linux support |
| **Sierra Wireless MC7455** | 4G LTE-A | 300 Mbps | ~$80 | Enterprise-grade, M.2 adapter needed |
| **Quectel EC25** | 4G LTE | 150 Mbps | ~$40 | Mini PCIe, USB adapter required |
| **Huawei E3531** | 3G HSPA+ | 21 Mbps | ~$15 | Budget option, older networks |

**Connection:**

```bash
# USB modem connects to Raspberry Pi USB port
# Appears as /dev/ttyUSB0, /dev/ttyUSB1, etc.
# Or as network interface (HiLink mode): usb0, wwan0
```

### Option 2: Android Phone as SMS Gateway

**Requirements:**

- Android 5.0+ device
- USB cable or WiFi connection
- SMS Gateway app (e.g., SMS Gateway API, Termux)

**Advantages:**

- Reuse old Android phone
- No additional hardware purchase
- Easy setup via app

### Option 3: Dedicated SIM800/SIM900 Module

**GSM/GPRS Modules:**

- **SIM800L** - 2G GSM, $5-10, GPIO/UART connection
- **SIM900A** - 2G GSM, $10-15, more stable
- **SIM7600** - 4G LTE, $30-40, modern networks

**Connection:**

```bash
# GPIO pins on Raspberry Pi
# TX/RX via UART: /dev/ttyAMA0 or /dev/serial0
```

---

## Software Setup

### 1. Install ModemManager (for USB modems)

```bash
# Install modem management tools
sudo apt update
sudo apt install modemmanager libqmi-utils libmbim-utils

# Check if modem is detected
sudo mmcli -L

# Get modem details
sudo mmcli -m 0

# Enable modem
sudo mmcli -m 0 --enable

# Check signal quality
sudo mmcli -m 0 --signal-get
```

### 2. Install Gammu (for SMS handling)

```bash
# Install Gammu SMS daemon
sudo apt install gammu gammu-smsd python3-gammu

# Configure Gammu
sudo nano /etc/gammu-smsdrc
```

**Gammu Configuration:**

```ini
[gammu]
device = /dev/ttyUSB0
connection = at
# For HiLink modems:
# device = /dev/ttyUSB2

[smsd]
service = files
logfile = /var/log/gammu-smsd.log
debuglevel = 1

# Inbox/outbox directories
inboxpath = /var/spool/gammu/inbox/
outboxpath = /var/spool/gammu/outbox/
sentsmspath = /var/spool/gammu/sent/
errorsmspath = /var/spool/gammu/error/
```

**Create directories:**

```bash
sudo mkdir -p /var/spool/gammu/{inbox,outbox,sent,error}
sudo chown -R gammu:gammu /var/spool/gammu
```

**Start Gammu daemon:**

```bash
sudo systemctl enable gammu-smsd
sudo systemctl start gammu-smsd
sudo systemctl status gammu-smsd
```

### 3. Python SMS Gateway Integration

```python
#!/usr/bin/env python3
"""
SMS Gateway for Privateness.network ENUM Backend
Handles SMS via USB modem or Android device
"""

import gammu
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSGateway:
    def __init__(self):
        self.state_machine = gammu.StateMachine()
        self.state_machine.ReadConfig()
        self.state_machine.Init()
        
    def send_sms(self, number, message):
        """Send SMS via modem"""
        try:
            sms_info = {
                'Text': message,
                'SMSC': {'Location': 1},
                'Number': number,
            }
            
            self.state_machine.SendSMS(sms_info)
            logger.info(f"SMS sent to {number}")
            return True
            
        except gammu.GSMError as e:
            logger.error(f"SMS send failed: {e}")
            return False
    
    def get_signal_strength(self):
        """Get modem signal strength"""
        try:
            signal = self.state_machine.GetSignalQuality()
            return {
                'signal_strength': signal['SignalStrength'],
                'signal_percent': signal['SignalPercent'],
                'bit_error_rate': signal['BitErrorRate']
            }
        except gammu.GSMError as e:
            logger.error(f"Signal check failed: {e}")
            return None

# Flask API endpoints
gateway = SMSGateway()

@app.route('/sms/send', methods=['POST'])
def send_sms():
    """Send SMS via modem"""
    data = request.json
    number = data.get('number')
    message = data.get('message')
    
    if not number or not message:
        return jsonify({'error': 'Missing number or message'}), 400
    
    success = gateway.send_sms(number, message)
    
    if success:
        return jsonify({'status': 'sent', 'number': number})
    else:
        return jsonify({'error': 'Failed to send SMS'}), 500

@app.route('/sms/signal', methods=['GET'])
def get_signal():
    """Get modem signal strength"""
    signal = gateway.get_signal_strength()
    
    if signal:
        return jsonify(signal)
    else:
        return jsonify({'error': 'Failed to get signal'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
```

**Save as:** `/home/pi/enum-server/sms_gateway_modem.py`

**Install dependencies:**

```bash
pip3 install python-gammu flask
```

**Run SMS gateway:**

```bash
python3 /home/pi/enum-server/sms_gateway_modem.py
```

### 4. Systemd Service for SMS Gateway

```ini
[Unit]
Description=SMS Gateway for Privateness.network
After=network.target gammu-smsd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/enum-server
ExecStart=/usr/bin/python3 /home/pi/enum-server/sms_gateway_modem.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save as:** `/etc/systemd/system/sms-gateway.service`

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable sms-gateway
sudo systemctl start sms-gateway
sudo systemctl status sms-gateway
```

---

## Integration with ENUM Backend

The SMS gateway runs **independently** from the ENUM backend. Integration points:

### 1. SMS 2FA Verification

When registering ENUM records, optionally verify phone number ownership via SMS:

```python
# In enum_backend.py - add SMS verification endpoint
@app.route('/enum/verify', methods=['POST'])
def verify_phone():
    """Send SMS verification code"""
    data = request.json
    phone_number = data.get('phone_number')
    
    # Generate verification code
    code = generate_verification_code()
    
    # Send via SMS gateway
    response = requests.post('http://localhost:8081/sms/send', json={
        'number': phone_number,
        'message': f'Privateness.network verification code: {code}'
    })
    
    if response.status_code == 200:
        # Store code in Redis/database for verification
        return jsonify({'status': 'sent'})
    else:
        return jsonify({'error': 'SMS send failed'}), 500
```

### 2. Emergency Fallback

Configure Antisip to use cellular fallback for emergency calls:

```json
{
  "enum_record": {
    "voice_primary": "sip:user@voip-server.com",
    "voice_fallback": "cellular:+1234567890",
    "emergency": "cellular:911"
  }
}
```

---

## Carrier SIM Considerations

### Choosing a Carrier

**For SMS 2FA:**

- ✅ **Prepaid SIM** - No contract, pay-as-you-go
- ✅ **Data-only SIM** - Some carriers offer SMS on data plans
- ✅ **IoT SIM** - Designed for M2M, often cheaper
- ⚠️ **VoIP detection** - Some carriers block VoIP, use separate SIM

**Recommended Carriers (US):**

- **T-Mobile Prepaid** - Good coverage, IoT-friendly
- **AT&T IoT** - Dedicated M2M plans
- **Google Fi** - Flexible, works internationally
- **Ting** - Low-cost, no contracts

**International:**

- **Twilio Super SIM** - Global coverage, programmable
- **Hologram** - IoT-focused, 550+ carriers
- **1NCE** - Flat-rate IoT SIM, 10-year validity

### SIM Activation

```bash
# Insert SIM into modem
# Check if SIM is detected
sudo mmcli -m 0 --sim 0

# Unlock SIM if PIN-protected
sudo mmcli -i 0 --pin=1234

# Check network registration
sudo mmcli -m 0 | grep state

# Should show: state: 'registered'
```

---

## Testing

### Test SMS Send

```bash
# Via Gammu CLI
echo "Test message from Privateness.network" | gammu sendsms TEXT +1234567890

# Via Python SMS gateway
curl -X POST http://localhost:8081/sms/send \
  -H "Content-Type: application/json" \
  -d '{"number": "+1234567890", "message": "Test from SMS gateway"}'
```

### Test Signal Strength

```bash
# Via ModemManager
sudo mmcli -m 0 --signal-get

# Via Python SMS gateway
curl http://localhost:8081/sms/signal
```

### Monitor SMS Logs

```bash
# Gammu logs
sudo tail -f /var/log/gammu-smsd.log

# SMS gateway logs
sudo journalctl -u sms-gateway -f
```

---

## Security Considerations

### 1. SIM Security

- ✅ **Enable SIM PIN** - Protect against physical theft
- ✅ **Disable unnecessary services** - Turn off voice if only using SMS
- ✅ **Monitor usage** - Set up alerts for unusual activity
- ⚠️ **SIM swapping** - Use carrier PIN/password protection

### 2. API Security

```bash
# Restrict SMS gateway to localhost
# In sms_gateway_modem.py:
app.run(host='127.0.0.1', port=8081)

# Or use firewall
sudo ufw deny 8081
sudo ufw allow from 127.0.0.1 to any port 8081
```

### 3. Rate Limiting

```python
# Add rate limiting to prevent SMS spam
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/sms/send', methods=['POST'])
@limiter.limit("10 per hour")  # Max 10 SMS per hour
def send_sms():
    # ... existing code
```

---

## Cost Analysis

### Hardware Costs

| Item | Price | Notes |
|------|-------|-------|
| USB 4G Modem | $30-80 | One-time purchase |
| Carrier SIM | $0-10 | Activation fee |
| USB Extension Cable | $5 | Optional, better signal |
| **Total** | **$35-95** | |

### Operating Costs

**SMS-only usage:**

- **Prepaid SIM**: $10-20/month (100-500 SMS)
- **IoT SIM**: $2-5/month (50-100 SMS)
- **Pay-per-SMS**: $0.01-0.05 per message

### Example: 2FA verification service

- 100 verifications/month × $0.02/SMS = **$2/month**
- Much cheaper than Twilio ($0.0079/SMS + $1.15/month phone number)

---

## Troubleshooting

### Modem Not Detected

```bash
# Check USB connection
lsusb | grep -i modem

# Check kernel messages
dmesg | grep -i usb

# Try different USB port
# Some modems need USB 2.0, not 3.0
```

### No Network Registration

```bash
# Check SIM status
sudo mmcli -m 0 --sim 0

# Manually scan networks
sudo mmcli -m 0 --3gpp-scan

# Force network selection
sudo mmcli -m 0 --3gpp-register-in-operator=310260  # T-Mobile US
```

### SMS Send Fails

```bash
# Check Gammu configuration
gammu identify

# Test AT commands directly
sudo gammu-detect

# Check SMSC number
gammu getsms 0
```

---

## Summary

**SIM Gateway is OPTIONAL for Privateness.network:**

✅ **Core ENUM backend works perfectly without SIM gateway**

- Decentralized VoIP via Emercoin NVS
- No cellular dependency
- Pure blockchain-based routing

🔧 **Add SIM gateway only if you need:**

- SMS 2FA verification (Telegram, WhatsApp, banks)
- Emergency services (E911/E112)
- Cellular fallback for poor VoIP coverage
- Geographic compliance (local carrier requirements)

💰 **Cost-effective:**

- ~$50 hardware (one-time)
- ~$2-10/month operating costs
- Much cheaper than commercial SMS APIs

🔒 **Security:**

- Runs isolated from core ENUM backend
- Optional rate limiting and access controls
- SIM PIN protection recommended

**For most Privateness.network deployments, the SIM gateway is NOT needed.**
