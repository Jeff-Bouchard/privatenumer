# Privateness Network Service Tiers

## Overview

Privateness.network offers **two service tiers** to meet different privacy and communication needs:

1. **SMS-only** — Verification and notifications
2. **SMS+Voice/Video** — Full communication suite

---

## 📱 SMS-only Tier

### Use Cases

- Account verification (social media, exchanges, services)
- Two-factor authentication (2FA)
- One-time password (OTP) reception
- Automated notifications
- Privacy-conscious users who don't need voice/video

### Features

✅ Real SIM card (non-VOIP)  
✅ Instant SMS delivery  
✅ E2E encrypted message content  
✅ Blind listing privacy (no phone number exposure)  
✅ RANDPAY micropayments  
❌ No voice calls  
❌ No video calls  
❌ No phone number assignment (receive-only)

### Pricing (Example)

- Per SMS: 0.001 EMC
- Daily rental: 0.01 EMC
- Weekly rental: 0.05 EMC
- Monthly rental: 0.15 EMC

### Technical Details

**Capabilities bitfield:** `11` (0x0B)

- Bit 0 (1): non-VOIP
- Bit 1 (2): instant delivery
- Bit 3 (8): SMS-only tier

**Flow:**

```
Sender → Provider SIM → Gateway → Skywire → Renter (encrypted SMS)
```

**What renter gets:**

- Access to encrypted SMS inbox via gateway
- No phone number to give out (receive-only)
- Rental duration confirmation

---

## 📞 SMS+Voice/Video Tier

### Use Cases

- Full phone number replacement
- Business communication
- Personal calls with privacy
- Video conferencing
- Giving out a "real" number to contacts

### Features

✅ All SMS-only features  
✅ Voice calls (inbound + outbound)  
✅ Video calls (H.264, VP8, VP9)  
✅ Real E.164 phone number assignment  
✅ SIP client integration (Antisip, Linphone)  
✅ Caller ID (outbound shows rented number)  
✅ ENUM support (optional)  
✅ Routed via Skywire (metadata privacy)

### Pricing (Example)

- Per SMS: 0.001 EMC
- Per minute (voice): 0.01 EMC
- Per minute (video): 0.02 EMC
- Daily rental: 0.05 EMC
- Weekly rental: 0.25 EMC
- Monthly rental: 0.80 EMC

### Technical Details

**Capabilities bitfield:** `123` (0x7B)

- Bit 0 (1): non-VOIP
- Bit 1 (2): instant delivery
- Bit 2 (4): region-us
- Bit 3 (8): SMS-only tier
- Bit 4 (16): voice calls
- Bit 5 (32): video calls
- Bit 6 (64): ENUM/SIP routing

**Flow:**

```
Caller → Provider SIM → Gateway → Skywire → Renter's SIP client
```

**What renter gets:**

- Real phone number (e.g., +1234567890)
- SIP credentials (username, password, server)
- Antisip/Linphone configuration file
- Rental duration and pricing
- Ability to give out number to contacts

**Number assignment:**

- Provider assigns from their pool (off-chain)
- Renter receives actual E.164 number
- Number returns to pool after rental expires
- Renter can renew or get different number

---

## Comparison Table

| Feature | SMS-only | SMS+Voice/Video |
|---------|----------|-----------------|
| **SMS reception** | ✅ | ✅ |
| **Voice calls** | ❌ | ✅ |
| **Video calls** | ❌ | ✅ |
| **Phone number** | ❌ (receive-only) | ✅ (full E.164) |
| **Outbound calls** | ❌ | ✅ |
| **SIP client** | Not needed | Required |
| **Caller ID** | N/A | Shows rented number |
| **ENUM support** | ❌ | ✅ (optional) |
| **Daily cost** | ~0.01 EMC | ~0.05 EMC |
| **Monthly cost** | ~0.15 EMC | ~0.80 EMC |

---

## How to Choose

### Choose SMS-only if

- You only need SMS verification/2FA
- You don't want to manage a SIP client
- You want the lowest cost
- You don't need to give out a number

### Choose SMS+Voice/Video if

- You need a full phone number replacement
- You want to make/receive calls
- You want video calling capability
- You need to give a number to contacts
- You're comfortable with SIP clients

---

## Technical Architecture

### SMS-only Architecture

```
Provider SIM → Gateway → Skywire → Renter (HTTPS/WSS)
```

**Renter interface:**

- Web dashboard or API
- Receives encrypted SMS
- No SIP client needed

### SMS+Voice/Video Architecture

```
Provider SIM → Gateway → Skywire → Renter (SIP client)
                                    ↓
                            Antisip/Linphone
```

**Renter interface:**

- SIP client (Antisip, Linphone, etc.)
- Connects via Skywire to gateway
- Receives calls/SMS
- Makes outbound calls

---

## Privacy Guarantees

### Both Tiers

✅ Blind listings (no phone number on-chain)  
✅ E2E encryption for message content  
✅ Skywire transport (metadata privacy)  
✅ No IP exposure  
✅ RANDPAY (payment privacy)

### SMS-only Additional Privacy

✅ No phone number assignment (receive-only)  
✅ No SIP metadata  
✅ Simpler attack surface

### SMS+Voice/Video Privacy Notes

⚠️ Provider sees call metadata (destination, duration)  
⚠️ Renter knows the actual phone number  
⚠️ Contacts calling the number see it as "normal"  
✅ Audio/video encrypted if SRTP used  
✅ Connection via Skywire (no IP exposure)

---

## Setup Instructions

### SMS-only Setup

1. Rent a blind listing (SMS-only tier)
2. Receive access credentials
3. Access SMS inbox via web dashboard or API
4. No additional configuration needed

### SMS+Voice/Video Setup

1. Rent a blind listing (SMS+Voice/Video tier)
2. Receive:
   - Phone number (e.g., +1234567890)
   - SIP credentials
   - Antisip configuration file
3. Install SIP client:
   - **Linux/macOS:** Linphone, Antisip
   - **Windows:** Linphone, MicroSIP
   - **Android/iOS:** Linphone mobile app
4. Import configuration file
5. Test incoming call (provider can send test call)
6. Give out your number to contacts

---

## Economic Model

### Provider Economics

**SMS-only:**

- Lower overhead (no SIP infrastructure)
- Higher volume potential
- Simpler to operate

**SMS+Voice/Video:**

- Higher revenue per rental
- Requires SIP/Asterisk setup
- More complex but more valuable

### Renter Economics

**SMS-only:**

- Pay only for what you need
- No SIP client overhead
- Ideal for verification use cases

**SMS+Voice/Video:**

- Full phone replacement
- Higher cost justified by features
- Ideal for primary communication

---

## Future Tiers (Roadmap)

### Potential additions

- **SMS+Voice-only** (no video, mid-tier pricing)
- **Enterprise tier** (dedicated numbers, SLA, priority support)
- **Burner tier** (ultra-short rentals, 1-hour minimum)
- **International tier** (numbers from multiple countries)

---

## FAQ

**Q: Can I upgrade from SMS-only to SMS+Voice/Video?**  
A: Yes, contact the provider or use the gateway API to upgrade your rental.

**Q: What happens to my number when rental expires?**  
A: It returns to the provider's pool. You can renew before expiration to keep it.

**Q: Can I port my existing number?**  
A: No, this is a rental service. You receive a number from the provider's pool.

**Q: Is voice/video quality good?**  
A: Yes, uses standard SIP/RTP protocols. Quality depends on your internet connection and Skywire routing.

**Q: Do I need to install anything for SMS-only?**  
A: No, just access the web dashboard or use the API.

**Q: What SIP clients are recommended?**  
A: Antisip (privacy-focused), Linphone (cross-platform), or any standard SIP client.

**Q: Can the provider listen to my calls?**  
A: Provider sees metadata (who you call, duration) but audio is encrypted if you use SRTP. For maximum privacy, both parties should use SIP/SRTP.

**Q: How does Skywire protect my privacy?**  
A: Multi-hop encrypted routing hides your IP address and prevents traffic analysis. Provider and gateway cannot see your source IP.

---

## Support

- Documentation: <https://github.com/ness-network/privatenumer>
- Gateway: <https://gateway.ness.cx>
- EmerDNS: <https://gateway.private.ness>
