# Renter Quickstart — Using SMS/Voice Service

**Role:** You want to receive SMS/calls privately without exposing your real phone number.

**Platform:** Android/iOS (mobile-first)

**Time:** ~5 minutes setup

---

## What You Need

1. **Antisip app** (SMS/voice client)
2. **Privateness Wallet** (for EMC payments)
3. **EMC balance** (~0.15 EMC for monthly SMS-only, ~0.80 EMC for monthly SMS+Voice/Video)

---

## Step 1: Install Apps

### Android

1. **Antisip:**
   - Download: [antisip.app](https://antisip.app) or Google Play
   - Permissions needed: Internet, Storage (for encrypted backups)

2. **Privateness Wallet:**
   - Download: [wallet.ness.cx](https://wallet.ness.cx) or Google Play
   - Permissions needed: Internet, Storage

### iOS

1. **Antisip:**
   - Download: [antisip.app](https://antisip.app) or App Store
   - Permissions needed: Internet, iCloud (optional, for backup)

2. **Privateness Wallet:**
   - Download: [wallet.ness.cx](https://wallet.ness.cx) or App Store
   - Permissions needed: Internet, iCloud (optional)

---

## Step 2: Fund Your Wallet

### Option A: Buy EMC

1. Open **Privateness Wallet**
2. Tap **Receive** → Copy your EMC address
3. Buy EMC from exchange:
   - [Bittrex](https://bittrex.com) (EMC/BTC, EMC/USDT)
   - [HitBTC](https://hitbtc.com) (EMC/BTC)
   - [Atomars](https://atomars.com) (EMC/BTC)
4. Withdraw to your wallet address
5. Wait for confirmations (~10 minutes)

### Option B: Receive from Friend

1. Open **Privateness Wallet**
2. Tap **Receive** → Show QR code
3. Friend scans and sends EMC
4. Done!

**Recommended balance:** 1-2 EMC (covers several months)

---

## Step 3: Create Identity (in Antisip)

1. Open **Antisip**
2. Tap **Get Started**
3. Tap **Create New Identity**
4. App generates:
   - Ed25519 keypair (for signatures)
   - X25519 keypair (for encryption)
5. **IMPORTANT:** Tap **Backup Identity**
   - Save encrypted backup to device
   - Optional: Export to Privateness Wallet for cross-device sync
6. Done! Your identity is ready.

**No passwords, no seed phrases, no manual key management.**

---

## Step 4: Browse Listings

1. In **Antisip**, tap **Browse Listings**
2. Filter by:
   - **Service tier:**
     - 📱 **SMS-only** (~0.01 EMC/day) — For verification, 2FA
     - 📞 **SMS+Voice/Video** (~0.05 EMC/day) — Full phone replacement
   - **Region:** USA, Europe, Asia, etc.
   - **Price range:** Set max daily/weekly/monthly cost
   - **Provider reputation:** ⭐⭐⭐⭐⭐ (5-star rating)
3. Tap a listing to view details:
   - Provider info (WORM lookup)
   - Service tier features
   - Pricing breakdown
   - Off-chain record (auto-fetched)
   - ✅ Commitment verified (automatic)
   - ✅ Signature verified (automatic)

---

## Step 5: Rent a Listing

1. Tap **Rent This Listing**
2. Choose duration:
   - **Daily** (flexible, higher per-day cost)
   - **Weekly** (recommended for testing)
   - **Monthly** (best value)
3. Review total cost
4. Tap **Pay with Privateness Wallet**
5. Wallet opens automatically
6. Choose payment method:
   - **RANDPAY** (1 EMC, 1/6 probability) — Instant, probabilistic
   - **Escrow** (full amount locked) — Guaranteed, for longer rentals
7. Confirm payment
8. Done! Listing is now active.

**For SMS+Voice/Video tier:**
- App auto-configures SIP client
- You receive a real phone number (e.g., +1234567890)
- Tap **My Number** to view it
- Give this number to contacts!

---

## Step 6: Receive SMS/Calls (Automatic)

### SMS-only tier:

**How it works:**
1. Someone sends SMS to provider's real SIM
2. Provider encrypts + signs → forwards to gateway
3. Gateway routes via Skywire to your Antisip app
4. App decrypts + verifies signature
5. You see SMS in **Antisip → Inbox**

**You don't do anything — it just appears!**

### SMS+Voice/Video tier:

**Same as above, plus:**

**Voice calls:**
- Incoming call rings in Antisip (like a normal phone)
- Tap **Answer** to pick up
- Audio routed via SIP over Skywire
- Caller doesn't know it's rented (looks like normal number)

**Outbound calls:**
- Tap **Dial** in Antisip
- Enter number
- Call goes: Antisip → Skywire → Gateway → Provider SIM → PSTN
- Caller ID shows your rented number

**Video calls:**
- Same as voice, but with camera
- Codecs: H.264, VP8, VP9
- Bandwidth: ~1-2 Mbps

---

## Step 7: Manage Rentals

### View active rentals

1. Tap **Antisip → My Rentals**
2. See:
   - Listing ID
   - Service tier
   - Expiration date
   - Days remaining
   - Total cost
   - SMS/call history

### Renew before expiration

1. Tap rental → **Renew**
2. Choose duration
3. Pay with Privateness Wallet
4. Done! Rental extended.

**Pro tip:** Enable **Auto-Renew** to never lose your number.

### Export receipts

1. Tap rental → **View Receipts**
2. See signed delivery proofs for each SMS/call
3. Tap **Export** → Save as JSON
4. Use for auditing or disputes

---

## Step 8: Give Out Your Number (Voice Tier Only)

**If you rented SMS+Voice/Video tier:**

1. Tap **Antisip → My Number**
2. See your assigned number (e.g., +1234567890)
3. Share with:
   - Friends/family
   - Business contacts
   - Online services
   - Anyone!

**They call/text this number → you receive in Antisip.**

**Privacy:** They don't know it's rented. Looks like a normal number.

---

## FAQ

### Q: How much EMC do I need?

**SMS-only:**
- Daily: 0.01 EMC
- Weekly: 0.05 EMC
- Monthly: 0.15 EMC

**SMS+Voice/Video:**
- Daily: 0.05 EMC
- Weekly: 0.25 EMC
- Monthly: 0.80 EMC

Plus per-message/minute fees (varies by provider).

### Q: What happens when rental expires?

- SMS-only: You lose access to inbox (but history saved locally)
- SMS+Voice/Video: Number returns to provider's pool
- **Renew before expiration to keep your number!**

### Q: Can I port my existing number?

No, this is a rental service. You receive a number from the provider's pool.

### Q: Is my data encrypted?

Yes! All SMS/call content is encrypted end-to-end:
- X25519 + ChaCha20-Poly1305 for SMS
- SRTP for voice/video (if both parties use SIP)
- Provider sees metadata (who you call, duration) but not content

### Q: Does this work internationally?

Yes! Listings are available from providers worldwide. Filter by region when browsing.

### Q: What if provider goes offline?

- Your rental remains valid (on-chain record)
- Find another provider with same tier
- Export your data before switching

### Q: Can I use multiple numbers?

Yes! Rent multiple listings. Each appears in **My Rentals**.

### Q: How do I get EMC?

Buy from exchanges (Bittrex, HitBTC, Atomars) or receive from friends.

### Q: Is this legal?

Depends on your jurisdiction. Using rented numbers for verification/privacy is generally legal. Check local laws.

---

## Troubleshooting

### App won't connect

1. Check internet connection
2. Try switching between WiFi and mobile data
3. Restart app
4. Check Skywire status (Settings → Network)

### SMS not arriving

1. Check rental is active (**My Rentals**)
2. Verify expiration date
3. Check provider reputation (may be offline)
4. Contact provider via gateway

### Voice calls not ringing

1. Check microphone/speaker permissions
2. Verify SMS+Voice/Video tier (not SMS-only)
3. Check SIP settings (Settings → Voice)
4. Test with provider's test number

### Payment failed

1. Check EMC balance in Privateness Wallet
2. Verify wallet is synced
3. Try RANDPAY instead of escrow (or vice versa)
4. Contact support

---

## Privacy Tips

### Maximum privacy:

1. **Use SMS-only tier** (no phone number assignment)
2. **Rotate listings** (rent different providers monthly)
3. **Don't link to personal info** (use burner email for account)
4. **Use Skywire exclusively** (no clearnet connections)
5. **Export and delete history** (don't keep logs in app)

### Moderate privacy:

1. **Use SMS+Voice/Video tier** (but rotate numbers quarterly)
2. **Give number only to trusted contacts**
3. **Use RANDPAY** (payment privacy)
4. **Enable auto-renew** (avoid gaps in service)

---

## Advanced: CLI/API Integration

If you want to integrate programmatically (not using Antisip app):

See [BLOCKCHAIN_SMS_ARCHITECTURE.md](BLOCKCHAIN_SMS_ARCHITECTURE.md) → "For Advanced Users (CLI/API)"

---

## Next Steps

- **Explore providers:** Browse listings, compare prices
- **Test SMS-only first:** Low cost, easy to try
- **Upgrade to voice:** If you need full phone replacement
- **Join community:** (TBD) Share tips, report issues

---

## Support

- **Docs:** [SERVICE_TIERS.md](SERVICE_TIERS.md)
- **Gateway:** https://gateway.ness.cx
- **Wallet:** https://wallet.ness.cx
- **Antisip:** https://antisip.app
